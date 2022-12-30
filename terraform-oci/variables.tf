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
  # Oracle Linux 8.6 - https://docs.oracle.com/en-us/iaas/images/image/93335573-b912-4796-b761-6aab2ecc73fa/
  default     = "ocid1.image.oc1.eu-frankfurt-1.aaaaaaaabnrabiyzoob3v2d63lwm5cuzr3q34cskuqewohkfsidxuyoutbma"
}
