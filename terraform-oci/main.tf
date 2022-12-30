terraform {
  required_providers {
    oci = {
      source  = "oracle/oci"
      version = ">= 4.102.0, < 5.0.0"
    }
  }
  cloud {
    organization = "Twixes"
    workspaces { name = "somsiad" }
  }
}

provider "oci" {
  tenancy_ocid = var.tenancy_ocid
  user_ocid    = var.user_ocid
  fingerprint  = var.fingerprint
  private_key  = var.private_key
  region       = var.region
}

locals {
  vcn_cidr_block            = "10.0.0.0/16"
  private_subnet_cidr_block = "10.0.1.0/24"
  public_subnet_cidr_block  = "10.0.0.0/24"
}

module "vcn" {
  source  = "oracle-terraform-modules/vcn/oci"
  version = "~> 3.5.3"

  compartment_id          = var.compartment_ocid
  label_prefix            = "somsiad"
  vcn_dns_label           = "somsiad"
  vcn_cidrs               = [local.vcn_cidr_block]
  create_internet_gateway = true
  create_nat_gateway      = true
  create_service_gateway  = true
}

resource "oci_core_security_list" "private_subnet_sl" {
  compartment_id = var.compartment_ocid
  vcn_id         = module.vcn.vcn_id
  display_name   = "somsiad-private-subnet-sl"

  egress_security_rules {
    stateless        = false
    destination      = "0.0.0.0/0"
    destination_type = "CIDR_BLOCK"
    protocol         = "all"
  }

  ingress_security_rules {
    stateless   = false
    source      = local.vcn_cidr_block
    source_type = "CIDR_BLOCK"
    protocol    = "all"
  }
}

resource "oci_core_security_list" "public_subnet_sl" {
  compartment_id = var.compartment_ocid
  vcn_id         = module.vcn.vcn_id
  display_name   = "somsiad-public-subnet-sl"

  egress_security_rules {
    stateless        = false
    destination      = "0.0.0.0/0"
    destination_type = "CIDR_BLOCK"
    protocol         = "all"
  }

  ingress_security_rules {
    stateless   = false
    source      = local.vcn_cidr_block
    source_type = "CIDR_BLOCK"
    protocol    = "all"
  }

  ingress_security_rules {
    stateless   = false
    source      = "0.0.0.0/0"
    source_type = "CIDR_BLOCK"
    protocol    = "6"
    tcp_options {
      min = 6443
      max = 6443
    }
  }
}

resource "oci_core_subnet" "vcn_private_subnet" {
  compartment_id             = var.compartment_ocid
  vcn_id                     = module.vcn.vcn_id
  cidr_block                 = local.private_subnet_cidr_block
  route_table_id             = module.vcn.nat_route_id
  security_list_ids          = [oci_core_security_list.private_subnet_sl.id]
  display_name               = "somsiad-private-subnet"
  prohibit_public_ip_on_vnic = true
}

resource "oci_core_subnet" "vcn_public_subnet" {
  compartment_id    = var.compartment_ocid
  vcn_id            = module.vcn.vcn_id
  cidr_block        = local.public_subnet_cidr_block
  route_table_id    = module.vcn.ig_route_id
  security_list_ids = [oci_core_security_list.public_subnet_sl.id]
  display_name      = "somsiad-public-subnet"
}

resource "oci_containerengine_cluster" "k8s_cluster" {
  compartment_id     = var.compartment_ocid
  kubernetes_version = "v1.24.1"
  name               = "somsiad-k8s-cluster"
  vcn_id             = module.vcn.vcn_id

  endpoint_config {
    is_public_ip_enabled = true
    subnet_id            = oci_core_subnet.vcn_public_subnet.id
  }

  options {
    add_ons {
      is_kubernetes_dashboard_enabled = true
      is_tiller_enabled               = false
    }
    kubernetes_network_config {
      pods_cidr     = "10.244.0.0/16"
      services_cidr = "10.96.0.0/16"
    }
    service_lb_subnet_ids = [oci_core_subnet.vcn_public_subnet.id]
  }
}

data "oci_identity_availability_domains" "ads" {
  compartment_id = var.compartment_ocid
}

resource "oci_containerengine_node_pool" "k8s_node_pool" {
  cluster_id     = oci_containerengine_cluster.k8s_cluster.id
  compartment_id = var.compartment_ocid
  name           = "somsiad-node-pool"
  node_shape     = "VM.Standard.A1.Flex"

  node_shape_config {
    memory_in_gbs = 6
    ocpus         = 1
  }

  node_source_details {
    image_id                = var.node_source_image_ocid
    source_type             = "image"
    boot_volume_size_in_gbs = 50
  }

  node_config_details {
    dynamic "placement_configs" {
      for_each = { for domain in data.oci_identity_availability_domains.ads.availability_domains : domain.id => domain.name }
      content {
        availability_domain = placement_configs.value
        subnet_id           = oci_core_subnet.vcn_private_subnet.id
      }
    }
    size = 2
  }

  initial_node_labels {
    key   = "name"
    value = "somsiad-cluster"
  }
}
