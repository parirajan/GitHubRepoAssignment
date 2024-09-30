stages:
  - validate

validate_package:
  stage: validate
  script:
    - echo "### Starting validation job ###"
    
    # Print the input variables passed from the Python script
    - echo "UPLOADED_FILE: $UPLOADED_FILE"
    - echo "CHECKSUM_FILE: $CHECKSUM_FILE"
    - echo "VERSION: $VERSION"
    - echo "DATE: $DATE"
    
    # Define the package registry URLs using the date and version
    - PACKAGE_URL="$CI_API_V4_URL/projects/$CI_PROJECT_ID/packages/generic/ccm/$DATE/$VERSION/$UPLOADED_FILE"
    - CHECKSUM_URL="$CI_API_V4_URL/projects/$CI_PROJECT_ID/packages/generic/ccm/$DATE/$VERSION/$CHECKSUM_FILE"
    
    # Echo the constructed URLs for debugging
    - echo "PACKAGE_URL: $PACKAGE_URL"
    - echo "CHECKSUM_URL: $CHECKSUM_URL"
    
    # Fetch the uploaded .iris file with --globoff to prevent globbing issues
    - echo "Fetching uploaded file from GitLab Package Registry..."
    - curl --globoff --header "PRIVATE-TOKEN: $CI_JOB_TOKEN" \
      --output downloaded_package.iris \
      "$PACKAGE_URL"
    
    # Fetch the checksum file (.cksum) with --globoff
    - echo "Fetching checksum file from GitLab Package Registry..."
    - curl --globoff --header "PRIVATE-TOKEN: $CI_JOB_TOKEN" \
      --output checksum_file.cksum \
      "$CHECKSUM_URL"
    
    # Extract expected checksum and filename from the checksum file
    - EXPECTED_CHECKSUM=$(grep "Checksum" checksum_file.cksum | awk -F': ' '{ print $2 }')
    - EXPECTED_FILENAME=$(grep "File" checksum_file.cksum | awk -F': ' '{ print $2 }')
    - echo "Expected checksum: $EXPECTED_CHECKSUM"
    - echo "Expected filename: $EXPECTED_FILENAME"
    
    # Validate the filename
    - |
      if [ "$EXPECTED_FILENAME" != "$UPLOADED_FILE" ]; then
        echo "Filename mismatch! Expected: $EXPECTED_FILENAME, Found: $UPLOADED_FILE"
        exit 1
      fi
    
    # Perform checksum validation on the downloaded .iris file
    - CALCULATED_CHECKSUM=$(sha256sum downloaded_package.iris | awk '{ print $1 }')
    - echo "Calculated checksum: $CALCULATED_CHECKSUM"
    
    # Compare the calculated checksum with the expected checksum
    - |
      if [ "$CALCULATED_CHECKSUM" != "$EXPECTED_CHECKSUM" ]; then
        echo "Checksum mismatch! Expected: $EXPECTED_CHECKSUM, Found: $CALCULATED_CHECKSUM"
        exit 1
      fi
    
    - echo "Validation complete: File checksum and filename match."
  only:
    - main
