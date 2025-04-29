# EC2 Security Configuration Guide

This guide provides instructions for configuring security settings for your EC2 instance hosting the Instagram Influencer Analyzer application.

## Configuring Inbound Rules

### Allow HTTP Access (Port 80)

1. Log in to the [AWS Management Console](https://console.aws.amazon.com/)
2. Navigate to EC2 Dashboard
3. Find your running instance (IP: 13.126.220.175)
4. Click on the Security tab
5. Click on the security group link (e.g., sg-xxxxxxxx)
6. Click "Edit inbound rules"
7. Click "Add rule" and configure:
   - Type: HTTP
   - Protocol: TCP
   - Port range: 80
   - Source: Anywhere (0.0.0.0/0) or specify your IP range for better security
8. Click "Save rules"
9. Verify by accessing your application at http://13.126.220.175

### Configure SSH Access (Port 22)

1. In the same Security Group settings, add or modify SSH rule:
   - Type: SSH
   - Protocol: TCP
   - Port range: 22
   - Source: Your IP address (recommended) or specify a trusted IP range
2. Click "Save rules"

## SSH Key Setup

1. Make sure your private key file has the correct permissions:
   ```
   chmod 400 ~/.ssh/insta_analyzer_key.pem
   ```

2. Connect to your instance using:
   ```
   ssh -i ~/.ssh/insta_analyzer_key.pem ec2-user@13.126.220.175
   ```

## Security Recommendations

1. **Use HTTPS**: Consider setting up SSL/TLS for secure connections
   - Request a certificate through AWS Certificate Manager
   - Configure your application or load balancer to use HTTPS (port 443)

2. **Restrict SSH Access**: Limit SSH access to specific trusted IP addresses

3. **Set Up Security Updates**:
   ```
   sudo yum update -y
   ```

4. **Enable AWS CloudWatch** for monitoring system metrics and logs

5. **Configure AWS Security Groups** as a firewall to control traffic

6. **Review IAM Permissions**: Ensure the EC2 instance has only necessary permissions

7. **Regular Backups**: Set up automated backups of your application data

## Troubleshooting

If you cannot connect to your instance:
1. Verify that your security group has the correct inbound rules
2. Check that you're using the correct key file
3. Ensure your IP address matches the allowed source in the security group
4. Confirm the instance is running by checking the EC2 Dashboard

For additional help, refer to [AWS EC2 Security Group Documentation](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ec2-security-groups.html) 