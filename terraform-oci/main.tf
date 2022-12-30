terraform {
  required_providers {
    oci = {
      source  = "hashicorp/oci"
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

resource "oci_core_vcn" "internal" {
  dns_label      = "internal"
  cidr_blocks    = ["172.16.0.0/24"]
  compartment_id = var.compartment_ocid
  display_name   = "Somsiad VCN"
}
