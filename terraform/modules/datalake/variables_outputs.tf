variable "storage_account_name" {
    type        = string
    description = "Globally unique storage account name for the data lake"
}

variable "resource_group_name" {
    type = string
}

variable "location" {
    type    = string
    default = "brazilsouth"
}

variable "tags" {
  type    = map(string)
  default = {}
}

output "storage_account_id" {
    value = azurerm_storage_account.datalake.id
}

output "primary_dfs_endpoint" {
  value = azurerm_storage_account.datalake.primary_dfs_endpoint
}
