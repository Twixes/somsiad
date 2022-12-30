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
  sensitive   = true
  nullable    = false
}

variable "region" {
  description = "OCI region identifier"
  type        = string
  nullable    = false
  default     = "eu-frankfurt-1"
}

variable "compartment_ocid" {
  description = "OCI compartment ID from https://cloud.oracle.com/identity/compartments"
  type        = string
  nullable    = false
}

variable "node_source_image_ocid" {
  description = "OCI image OCID from https://cloud.oracle.com/compute/images"
  type        = string
  nullable    = false
  # Oracle Linux 9.0 - https://docs.oracle.com/en-us/iaas/images/image/9801d535-f7a9-4051-9fbe-2df35ce229e0/
  default     = "ocid1.image.oc1.eu-frankfurt-1.aaaaaaaat5wpayf23ew5m2oilaq3sg6mnclfy62ukwb3br3z6jlmsha4wxnq"
}
