# Azure Cosmos DB Data-Plane RBAC Guide

When connecting to Azure Cosmos DB using Entra ID (via `DefaultAzureCredential`), traditional subscription-level roles like **Owner** or **Contributor** do not grant permission to read or write data inside the database. You must assign Cosmos DB data-plane roles explicitly.

## Grant Access Command

The following Azure CLI command was executed to grant read and write access to your principal ID on the Cosmos DB account:

```bash
az cosmosdb sql role assignment create \
  --account-name vovy-cosmosdb \
  --resource-group foundry-test1 \
  --role-definition-id 00000000-0000-0000-0000-000000000002 \
  --principal-id d1094455-6ec8-4144-8954-7502b7c1d11b \
  --scope "/"
```

---

## Parameter Explanation

| Parameter | Value / ID | Description |
| :--- | :--- | :--- |
| `--account-name` | `vovy-cosmosdb` | The name of your Cosmos DB account. |
| `--resource-group` | `foundry-test1` | The resource group containing your Cosmos DB account. |
| `--role-definition-id` | `00000000-0000-0000-0000-000000000002` | The unique definition ID of the **Azure Cosmos DB Built-in Data Contributor** role (allows full read/write operations). |
| `--principal-id` | `d1094455-6ec8-4144-8954-7502b7c1d11b` | The Entra ID Object ID of the user or system principal (e.g., your Azure CLI logged-in user or a Managed Identity). |
| `--scope` | `"/"` | The data access scope level. `"/"` allows access to the entire account (all databases/containers). |

---

## Why Is This Necessary?

Azure divides operations into two scopes:
1. **Management Plane**: Handled by Azure Resource Manager (ARM). Roles like *Owner* or *Contributor* allow you to manage the infrastructure (e.g., create/delete accounts, change network rules).
2. **Data Plane**: Handled directly by the Cosmos DB database engine. Accessing documents or database objects using passwordless Entra ID requires native SQL RBAC role assignments, which are independent of ARM roles.

*Note: For **Read-Only** access, you can replace the `--role-definition-id` with `00000000-0000-0000-0000-000000000001` (Azure Cosmos DB Built-in Data Reader).*
