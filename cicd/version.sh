#!/usr/bin/bash

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

while getopts mc flag
do
  case "${flag}" in
    m)
      metadata=true
      ;;
    c)
      cache=true
      ;;
  esac
done

cache_file=$(echo "$(dirname "${BASH_SOURCE[0]}")$(echo "/../.version-cache-date")")
version_config=$(cd "$(dirname "${BASH_SOURCE[0]}")" ; cat ../.version)
latest_tag_raw=$(git describe --tags --abbrev=0)
latest_tag_xyz=${latest_tag_raw:1}
latest_tag_array=(${latest_tag_xyz//./ })
latest_tag_x=${latest_tag_array[0]}
latest_tag_y=${latest_tag_array[1]}
latest_tag_z=${latest_tag_array[2]}
count_from_tag=$(git rev-list $latest_tag_raw..HEAD --count)

if [ "$count_from_tag" -eq 0 ] ; then
  # <version core>
  base_smver="$latest_tag_x.$latest_tag_y.$latest_tag_z"
else
  commit_id=$(git rev-parse --short HEAD)
  prerelease_smver="$count_from_tag.$commit_id"

  case "${version_config}" in
    major)
      latest_tag_x=$((latest_tag_x+1))
      latest_tag_y=0
      latest_tag_z=0
      ;;
    minor)
      latest_tag_y=$((latest_tag_y+1))
      latest_tag_z=0
      ;;
    patch)
      latest_tag_z=$((latest_tag_z+1))
      ;;
  esac

  # <version core> "-" <pre-release>
  base_smver="$latest_tag_x.$latest_tag_y.$latest_tag_z-$prerelease_smver"
fi

if [ "$metadata" = true ] ; then
  if [ "$cache" = true ] && [ -f $cache_file ] ; then
    build_date=$(cat "$cache_file")
  else
    build_date=$(date -u "+%Y%m%d%H%M%S")
    echo $build_date > "$cache_file"
  fi

  metadata_smver=$build_date
  echo "$base_smver+$metadata_smver"
else
  echo "$base_smver"
fi
