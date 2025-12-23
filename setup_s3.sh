#!/bin/bash

# AWS S3 Setup Script for HackerCast AI Podcast
# This script sets up an S3 bucket for podcast hosting

set -e  # Exit on any error

BUCKET_NAME="hackercast-ai-podcast"
REGION="us-east-1"

echo "=========================================="
echo "AWS S3 Setup for HackerCast AI Podcast"
echo "=========================================="
echo ""

# Check if AWS CLI is configured
if ! aws sts get-caller-identity &> /dev/null; then
    echo "❌ AWS CLI is not configured."
    echo ""
    echo "Please run: aws configure"
    echo ""
    echo "You'll need:"
    echo "1. AWS Access Key ID"
    echo "2. AWS Secret Access Key"
    echo "3. Default region (use: us-east-1)"
    echo "4. Default output format (use: json)"
    echo ""
    echo "Don't have an AWS account? Sign up at: https://aws.amazon.com/free/"
    exit 1
fi

echo "✅ AWS CLI is configured"
echo ""

# Get AWS account info
ACCOUNT_INFO=$(aws sts get-caller-identity)
ACCOUNT_ID=$(echo $ACCOUNT_INFO | python3 -c "import sys, json; print(json.load(sys.stdin)['Account'])")
USER_ARN=$(echo $ACCOUNT_INFO | python3 -c "import sys, json; print(json.load(sys.stdin)['Arn'])")

echo "AWS Account ID: $ACCOUNT_ID"
echo "User: $USER_ARN"
echo ""

# Check if bucket already exists
if aws s3 ls "s3://$BUCKET_NAME" 2>&1 | grep -q 'NoSuchBucket'; then
    echo "Creating S3 bucket: $BUCKET_NAME"
    
    # Create bucket
    if [ "$REGION" = "us-east-1" ]; then
        aws s3 mb "s3://$BUCKET_NAME"
    else
        aws s3 mb "s3://$BUCKET_NAME" --region "$REGION"
    fi
    
    echo "✅ Bucket created: $BUCKET_NAME"
else
    echo "✅ Bucket already exists: $BUCKET_NAME"
fi

echo ""
echo "Disabling Block Public Access settings..."
aws s3api put-public-access-block \
    --bucket "$BUCKET_NAME" \
    --public-access-block-configuration \
    "BlockPublicAcls=false,IgnorePublicAcls=false,BlockPublicPolicy=false,RestrictPublicBuckets=false"

echo "✅ Public access enabled"
echo ""
echo "Setting up bucket policy for public read access..."

# Create bucket policy file
cat > /tmp/bucket-policy.json << EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "PublicReadGetObject",
      "Effect": "Allow",
      "Principal": "*",
      "Action": "s3:GetObject",
      "Resource": "arn:aws:s3:::$BUCKET_NAME/*"
    }
  ]
}
EOF

# Apply bucket policy
aws s3api put-bucket-policy --bucket "$BUCKET_NAME" --policy file:///tmp/bucket-policy.json

echo "✅ Bucket policy applied (public read access)"
echo ""

# Test upload
echo "Testing upload with a small test file..."
echo "Test podcast episode" > /tmp/test.mp3
aws s3 cp /tmp/test.mp3 "s3://$BUCKET_NAME/test/test.mp3" \
    --content-type "audio/mpeg"

TEST_URL="https://$BUCKET_NAME.s3.$REGION.amazonaws.com/test/test.mp3"
echo "✅ Test file uploaded"
echo ""

# Verify MIME type
echo "Verifying content-type header..."
CONTENT_TYPE=$(curl -sI "$TEST_URL" | grep -i "content-type" | head -1)
echo "$CONTENT_TYPE"

if echo "$CONTENT_TYPE" | grep -q "audio/mpeg"; then
    echo "✅ Correct MIME type detected!"
else
    echo "⚠️  Warning: MIME type may not be correct"
fi

# Cleanup test file
aws s3 rm "s3://$BUCKET_NAME/test/test.mp3"
rm /tmp/test.mp3 /tmp/bucket-policy.json

echo ""
echo "=========================================="
echo "✅ S3 Setup Complete!"
echo "=========================================="
echo ""
echo "Bucket name: $BUCKET_NAME"
echo "Region: $REGION"
echo "Base URL: https://$BUCKET_NAME.s3.$REGION.amazonaws.com"
echo ""
echo "Next steps:"
echo "1. Update publish_podcast_s3.py with your bucket name (already set)"
echo "2. Run: python publish_podcast_s3.py --date 10162025"
echo ""
echo "Estimated monthly cost: $0.10-0.20"
echo "Estimated annual cost: $1.20-2.40"
echo ""
