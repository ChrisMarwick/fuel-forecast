resource "aws_resourcegroups_group" "rg" {
  name = "fuel-forecast-rg"

  resource_query {
    query = <<JSON
{
  "ResourceTypeFilters": ["AWS::AllSupported"],
  "TagFilters": [
    {
      "Key": "app",
      "Values": ["fuel-forecast"]
    }
  ]
}
JSON
  }
}

