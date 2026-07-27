terraform {
  required_version = ">= 1.6"
    required_providers {
        azurerm = {
              source  = "hashicorp/azurerm"
                    version = "~> 3.100"
                        }
                          }
                            backend "azurerm" {
                                # remote state - values supplied via -backend-config in CI (Azure DevOps)
                                  }
                                  }

                                  provider "azurerm" {
                                    features {}
                                    }

                                    locals {
                                      tags = {
                                          project     = "energy-data-pipeline"
                                              environment = "prod"
                                                  cost_center = "data-platform"
                                                      owner       = "kleidir.devops@gmail.com"
                                                        }
                                                        }

                                                        resource "azurerm_resource_group" "this" {
                                                          name     = "rg-energy-data-platform-prod"
                                                            location = "brazilsouth"
                                                              tags     = local.tags
                                                              }

                                                              module "datalake" {
                                                                source               = "../../modules/datalake"
                                                                  storage_account_name = "energydatalakeprod"
                                                                    resource_group_name  = azurerm_resource_group.this.name
                                                                      location             = azurerm_resource_group.this.location
                                                                        tags                 = local.tags
                                                                        }

                                                                        module "aks" {
                                                                          source              = "../../modules/aks"
                                                                            cluster_name        = "aks-energy-etl-prod"
                                                                              resource_group_name = azurerm_resource_group.this.name
                                                                                location            = azurerm_resource_group.this.location
                                                                                  dns_prefix          = "energy-etl-prod"
                                                                                    tags                = local.tags
                                                                                    }

                                                                                    output "datalake_endpoint" {
                                                                                      value = module.datalake.primary_dfs_endpoint
                                                                                      }

                                                                                      output "aks_cluster_id" {
                                                                                        value = module.aks.cluster_id
                                                                                        }
                                                                                        
