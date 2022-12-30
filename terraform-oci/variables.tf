variable "tenancy_ocid" {
  description = "OCI tenancy ID from https://cloud.oracle.com/identity/domains/my-profile/api-keys"
  type        = string
  nullable    = false
}

variable "user_ocid" {
  description = "OCI user ID from https://cloud.oracle.com/identity/domains/my-profile/api-keys"
  type        = string
  nullable    = false
}

variable "fingerprint" {
  description = "OCI API key fingerprint from https://cloud.oracle.com/identity/domains/my-profile/api-keys"
  type        = string
  nullable    = false
}

variable "private_key" {
  description = "OCI API key private key contents"
  type        = string
  sensitive = true
  nullable    = false
}

variable "region" {
  description = "OCI region identifier"
  type        = string
  nullable    = false
}

variable "compartment_ocid" {
  description = "OCI compartment ID from https://cloud.oracle.com/identity/compartments"
  type        = string
  nullable    = false
}
