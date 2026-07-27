# ADLS Gen2 data lake with bronze/silver/gold containers (medallion architecture)

  resource "azurerm_storage_account" "datalake" {
    name                     = var.storage_account_name
        resource_group_name      = var.resource_group_name
        location                 = var.location
        account_tier             = "Standard"
        account_replication_type = "LRS"
        account_kind             = "StorageV2"
        is_hns_enabled           = true

        tags = var.tags
}

resource "azurerm_storage_data_lake_gen2_filesystem" "bronze" {
    name               = "bronze"
        storage_account_id = azurerm_storage_account.datalake.id
}

resource "azurerm_storage_data_lake_gen2_filesystem" "silver" {
    name               = "silver"
        storage_account_id = azurerm_storage_account.datalake.id
}

resource "azurerm_storage_data_lake_gen2_filesystem" "gold" {
    name               = "gold"
        storage_account_id = azurerm_storage_account.datalake.id
}

resource "azurerm_storage_management_policy" "lifecycle" {
    storage_account_id = azurerm_storage_account.datalake.id

        rule {
          name    = "bronze-tiering"
                enabled = true

                filters {
                  prefix_match = ["bronze/"]
                          blob_types   = ["blockBlob"]
          }

          actions {
                  base_blob {
                            tier_to_cool_after_days_since_modification_greater_than    = 30
                                      tier_to_archive_after_days_since_modification_greater_than = 180
                  }
          }
    }
}
