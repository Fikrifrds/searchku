# AWS S3 Setup for Page Images

This guide explains how to set up AWS S3 for storing page images generated from PDF uploads.

## Prerequisites

- AWS Account
- AWS CLI configured (optional but recommended)
- S3 bucket created

## Step 1: Create S3 Bucket

1. Go to AWS S3 Console
2. Click "Create bucket"
3. Choose a unique bucket name (e.g., `searchku-page-images`)
4. Select your preferred region (e.g., `us-east-1`)
5. Configure public access settings:
   - **Uncheck** "Block all public access" if you want direct image access
   - Or keep it checked and use signed URLs (more secure)
6. Enable versioning (optional)
7. Click "Create bucket"

## Step 2: Create IAM User (Recommended)

1. Go to AWS IAM Console
2. Click "Users" → "Add user"
3. Enter username (e.g., `searchku-s3-user`)
4. Select "Programmatic access"
5. Click "Next: Permissions"
6. Choose "Attach existing policies directly"
7. Search and select: `AmazonS3FullAccess` (or create custom policy)
8. Click through to create user
9. **Save the Access Key ID and Secret Access Key**

## Step 3: Configure Environment Variables

Update your `.env` file with the AWS credentials:

```env
# AWS S3 Configuration for Page Images
AWS_ACCESS_KEY_ID=your_access_key_here
AWS_SECRET_ACCESS_KEY=your_secret_key_here
AWS_REGION=us-east-1
AWS_S3_BUCKET_NAME=your-bucket-name
```

## Step 4: Bucket Policy (Optional - for public access)

If you want images to be publicly accessible, add this bucket policy:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "PublicReadGetObject",
            "Effect": "Allow",
            "Principal": "*",
            "Action": "s3:GetObject",
            "Resource": "arn:aws:s3:::your-bucket-name/*"
        }
    ]
}
```

## Step 5: Test the Setup

1. Start your application
2. Upload a PDF file through the web interface
3. Check the logs for S3 upload messages
4. Verify images appear in your S3 bucket
5. Check that page responses include `page_image_url` field

## Image Organization

Images are organized in S3 as follows:
```
your-bucket/
  pages/
    book_1/
      page_1_uuid.png
      page_2_uuid.png
    book_2/
      page_1_uuid.png
      ...
```

## Troubleshooting

### Common Issues

1. **S3 service not available**: Check AWS credentials and bucket name
2. **Access denied**: Verify IAM permissions
3. **Images not appearing**: Check bucket policy for public access
4. **Upload fails**: Verify bucket exists and credentials are correct

### Logs to Check

- Application logs for S3 upload messages
- AWS CloudTrail for API calls (if enabled)
- S3 access logs (if enabled)

## Security Best Practices

1. Use IAM user with minimal required permissions
2. Enable MFA for AWS account
3. Use signed URLs instead of public bucket access
4. Enable CloudTrail for API monitoring
5. Regularly rotate access keys
6. Use VPC endpoints for S3 access (in production)

## Cost Optimization

1. Set up lifecycle policies to archive old images
2. Use S3 Intelligent Tiering for automatic cost optimization
3. Monitor usage with AWS Cost Explorer
4. Consider using CloudFront CDN for better performance

## Production Considerations

1. Enable versioning for backup/recovery
2. Set up cross-region replication for disaster recovery
3. Use CloudFront for global content delivery
4. Implement proper error handling and retry logic
5. Monitor with CloudWatch metrics