###
# SmVer version generator based on current commit.
#
# Requires to enable these Git features: unshallow fetch, fetch tags. Output difer from the Git environment:
#
#   - If the tag is added on the current commit, output follows <version core>, or <version core> "+" <build>.
#   - If the tag is added on an ancestor, this build is treaten as a pre-release, output follows <version core> "-" <pre-release>, or <version core> "-" <pre-release> "+" <build>. The pre-release is greater than the previous commit. Choice between patch, minor or major version increment is stored in the ".version" file.
#
# Parameters:
#
#   -m    Displays build metadata (<version core> "+" <build>, or <version core> "-" <pre-release> "+" <build>)
#   -c    Cache the date contained in the metadata. Data is stored in the ".version-cache-date" file. Alloys re-executing the command multiple times with a reproductible response, like in CI/CD environment.
#
# Usage:
#
#   - Without metadata: "bash version.sh"
#   - With metadata: bash version.sh -b
#
# See: https://semver.org/#backusnaur-form-grammar-for-valid-semver-versions
###

$metadata = $false
$cache = $false

for ($i = 0; $i -lt $args.Length; $i++) {
  $arg = $args[$i]
  if ($arg -eq "-m") {
    $metadata = $true
  }
  elseif ($arg -eq "-c") {
    $cache = $true
  }
  else {
    throw "Unknown parameter: $arg"
  }
}

$cache_file = "$(Split-Path $MyInvocation.MyCommand.Definition)/../.version-cache-date"
$version_config = Get-Content "$(Split-Path $MyInvocation.MyCommand.Definition)/../.version"
$latest_tag_raw = git describe --tags --abbrev=0 --match "v[0-9].[0-9].[0-9]"
$latest_tag_xyz = $latest_tag_raw.TrimStart("v")
$latest_tag_array = $latest_tag_xyz.Split(".")
$latest_tag_x = [int] $latest_tag_array[0]
$latest_tag_y = [int] $latest_tag_array[1]
$latest_tag_z = [int] $latest_tag_array[2]
$count_from_tag = git rev-list "$latest_tag_raw..HEAD" --count

if ($count_from_tag -eq 0) {
  $base_smver = "$latest_tag_x.$latest_tag_y.$latest_tag_z"
} else {
  $commit_id = git rev-parse --short HEAD
  $prerelease_smver = "$count_from_tag.$commit_id"

  switch ($version_config) {
    "major" {
      $latest_tag_x++
      $latest_tag_y = 0
      $latest_tag_z = 0
      break
    }
    "minor" {
      $latest_tag_y++
      $latest_tag_z = 0
      break
    }
    "patch" {
      $latest_tag_z++
      break
    }
    default {
      throw "Unknown version config: $version_config"
    }
  }

  $base_smver = "$latest_tag_x.$latest_tag_y.$latest_tag_z-$prerelease_smver"
}

if ( $metadata -eq $true ) {
  if ( $cache -eq $true -and (Test-Path $cache_file) ) {
    $build_date = Get-Content $cache_file
  } else {
    $build_date = (Get-Date).ToUniversalTime().ToString("yyyyMMddHHmmss")
    Set-Content $cache_file $build_date
  }
  $metadata_smver = $build_date
  Write-Output "$base_smver+$metadata_smver"
} else {
  Write-Output "$base_smver"
}
