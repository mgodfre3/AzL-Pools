// AzL Pools — Main Bicep template
// Deploys: Function App, PostgreSQL, Storage, App Insights, Azure OpenAI

@description('Base name for all resources')
param baseName string = 'azlpools'

@description('Azure region')
param location string = resourceGroup().location

@description('ATTOM Data API key')
@secure()
param attomApiKey string

@description('Bing Maps API key')
@secure()
param bingMapsKey string

@description('Melissa Data API key (optional)')
@secure()
param melissaApiKey string = ''

@description('PostgreSQL administrator password')
@secure()
param dbPassword string

@description('Azure OpenAI endpoint (optional — leave blank to skip)')
param azureOpenAiEndpoint string = ''

@description('Azure OpenAI API key')
@secure()
param azureOpenAiKey string = ''

@description('Azure OpenAI deployment name')
param azureOpenAiDeployment string = 'phi-4-mini'

@description('Function App SKU')
@allowed(['Y1', 'EP1', 'EP2'])
param functionPlanSku string = 'EP1'

var uniqueSuffix = uniqueString(resourceGroup().id, baseName)
var storageName = '${baseName}st${uniqueSuffix}'
var funcAppName = '${baseName}-func-${uniqueSuffix}'
var serverFarmName = '${baseName}-plan-${uniqueSuffix}'
var dbServerName = '${baseName}-db-${uniqueSuffix}'
var appInsightsName = '${baseName}-ai-${uniqueSuffix}'
var logWorkspaceName = '${baseName}-log-${uniqueSuffix}'

// ---------- Log Analytics ----------
resource logWorkspace 'Microsoft.OperationalInsights/workspaces@2022-10-01' = {
  name: logWorkspaceName
  location: location
  properties: {
    sku: { name: 'PerGB2018' }
    retentionInDays: 30
  }
}

// ---------- Application Insights ----------
resource appInsights 'Microsoft.Insights/components@2020-02-02' = {
  name: appInsightsName
  location: location
  kind: 'web'
  properties: {
    Application_Type: 'web'
    WorkspaceResourceId: logWorkspace.id
  }
}

// ---------- Storage Account (Functions runtime + queues) ----------
resource storageAccount 'Microsoft.Storage/storageAccounts@2023-01-01' = {
  name: storageName
  location: location
  sku: { name: 'Standard_LRS' }
  kind: 'StorageV2'
  properties: {
    supportsHttpsTrafficOnly: true
    minimumTlsVersion: 'TLS1_2'
  }
}

// ---------- PostgreSQL Flexible Server ----------
resource dbServer 'Microsoft.DBforPostgreSQL/flexibleServers@2023-06-01-preview' = {
  name: dbServerName
  location: location
  sku: {
    name: 'Standard_B1ms'
    tier: 'Burstable'
  }
  properties: {
    version: '16'
    administratorLogin: 'poolprospect'
    administratorLoginPassword: dbPassword
    storage: { storageSizeGB: 32 }
    backup: {
      backupRetentionDays: 7
      geoRedundantBackup: 'Disabled'
    }
    highAvailability: { mode: 'Disabled' }
  }
}

resource dbFirewallAllowAzure 'Microsoft.DBforPostgreSQL/flexibleServers/firewallRules@2023-06-01-preview' = {
  parent: dbServer
  name: 'AllowAzureServices'
  properties: {
    startIpAddress: '0.0.0.0'
    endIpAddress: '0.0.0.0'
  }
}

resource database 'Microsoft.DBforPostgreSQL/flexibleServers/databases@2023-06-01-preview' = {
  parent: dbServer
  name: 'poolprospect'
}

// ---------- App Service Plan (Functions) ----------
resource serverFarm 'Microsoft.Web/serverfarms@2023-01-01' = {
  name: serverFarmName
  location: location
  sku: {
    name: functionPlanSku
    tier: functionPlanSku == 'Y1' ? 'Dynamic' : 'ElasticPremium'
  }
  kind: 'linux'
  properties: {
    reserved: true
  }
}

// ---------- Function App ----------
resource functionApp 'Microsoft.Web/sites@2023-01-01' = {
  name: funcAppName
  location: location
  kind: 'functionapp,linux'
  properties: {
    serverFarmId: serverFarm.id
    siteConfig: {
      linuxFxVersion: 'Python|3.12'
      appSettings: [
        { name: 'AzureWebJobsStorage'; value: 'DefaultEndpointsProtocol=https;AccountName=${storageAccount.name};AccountKey=${storageAccount.listKeys().keys[0].value}' }
        { name: 'FUNCTIONS_EXTENSION_VERSION'; value: '~4' }
        { name: 'FUNCTIONS_WORKER_RUNTIME'; value: 'python' }
        { name: 'APPINSIGHTS_INSTRUMENTATIONKEY'; value: appInsights.properties.InstrumentationKey }
        { name: 'DATABASE_URL'; value: 'postgresql://poolprospect:${dbPassword}@${dbServer.properties.fullyQualifiedDomainName}:5432/poolprospect?sslmode=require' }
        { name: 'ATTOM_API_KEY'; value: attomApiKey }
        { name: 'BING_MAPS_KEY'; value: bingMapsKey }
        { name: 'MELISSA_API_KEY'; value: melissaApiKey }
        { name: 'AZURE_OPENAI_ENDPOINT'; value: azureOpenAiEndpoint }
        { name: 'AZURE_OPENAI_KEY'; value: azureOpenAiKey }
        { name: 'AZURE_OPENAI_DEPLOYMENT'; value: azureOpenAiDeployment }
        { name: 'DETECTION_THRESHOLD'; value: '0.5' }
      ]
      ftpsState: 'Disabled'
    }
    httpsOnly: true
  }
}

// ---------- Outputs ----------
output functionAppName string = functionApp.name
output functionAppUrl string = 'https://${functionApp.properties.defaultHostName}'
output dbServerFqdn string = dbServer.properties.fullyQualifiedDomainName
output storageAccountName string = storageAccount.name
output appInsightsKey string = appInsights.properties.InstrumentationKey
