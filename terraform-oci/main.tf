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
  vcn_cidr_block = "10.0.0.0/16"
  private_subnet_cidr_block = "10.0.1.0/24"
  public_subnet_cidr_block = "10.0.0.0/24"
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
  display_name = "somsiad-public-subnet-sl"
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
  compartment_id = var.compartment_ocid
  vcn_id         = module.vcn.vcn_id
  cidr_block     = local.private_subnet_cidr_block
  route_table_id             = module.vcn.nat_route_id
  security_list_ids          = [oci_core_security_list.private_subnet_sl.id]
  display_name               = "somsiad-private-subnet"
  prohibit_public_ip_on_vnic = true
}

resource "oci_core_subnet" "vcn_public_subnet" {
  compartment_id = var.compartment_ocid
  vcn_id         = module.vcn.vcn_id
  cidr_block     = local.public_subnet_cidr_block
  route_table_id    = module.vcn.ig_route_id
  security_list_ids = [oci_core_security_list.public_subnet_sl.id]
  display_name      = "somsiad-public-subnet"
}
