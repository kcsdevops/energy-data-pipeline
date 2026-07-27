# AKS cluster sized for batch/ETL job workloads.
# The "jobs" user node pool scales to zero when idle - job clusters spin up
# only when a bronze/silver/gold stage is triggered, and scale back down
# once the run completes.

resource "azurerm_kubernetes_cluster" "this" {
  name                = var.cluster_name
  location            = var.location
  resource_group_name = var.resource_group_name
  dns_prefix          = var.dns_prefix

  default_node_pool {
    name       = "system"
    vm_size    = "Standard_D2s_v5"
    node_count = 2
    zones      = ["1", "2", "3"]
  }

  identity {
    type = "SystemAssigned"
  }

  network_profile {
    network_plugin = "azure"
    network_policy = "azure"
  }

  tags = var.tags
}

resource "azurerm_kubernetes_cluster_node_pool" "jobs" {
  name                  = "jobs"
  kubernetes_cluster_id = azurerm_kubernetes_cluster.this.id
  vm_size               = var.job_node_vm_size
  enable_auto_scaling   = true
  min_count             = 0
  max_count             = var.job_node_max_count
  node_labels = {
    workload = "etl-medallion"
  }
  node_taints = [
    "workload=etl-medallion:NoSchedule"
  ]

  tags = var.tags
}

variable "cluster_name" {
  type = string
}

variable "resource_group_name" {
  type = string
}

variable "location" {
  type    = string
  default = "brazilsouth"
}

variable "dns_prefix" {
  type = string
}

variable "job_node_vm_size" {
  type    = string
  default = "Standard_D4s_v5"
}

variable "job_node_max_count" {
  type    = number
  default = 6
}

variable "tags" {
  type    = map(string)
  default = {}
}

output "cluster_id" {
  value = azurerm_kubernetes_cluster.this.id
}

output "kube_config" {
  value     = azurerm_kubernetes_cluster.this.kube_config_raw
  sensitive = true
}
