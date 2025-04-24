# Wiki7 Architecture

This document outlines the architecture and infrastructure design for the Wiki7 project.

## System Overview

Wiki7 is built on MediaWiki with custom extensions and skins, deployed on AWS using containerization and managed services. The architecture focuses on scalability, reliability, security, and ease of maintenance.

## Infrastructure Components

### AWS Services

The infrastructure leverages the following AWS services:

1. **Amazon ECS (Elastic Container Service)**
   - Container orchestration for MediaWiki application
   - Managed Fargate compute for serverless container deployment
   - Auto-scaling based on demand

2. **Amazon RDS (Relational Database Service)**
   - MySQL database for MediaWiki
   - Multi-AZ deployment for high availability
   - Automated backups and maintenance

3. **Amazon S3 (Simple Storage Service)**
   - Storage for wiki media files (images, videos, documents)
   - Version control of uploaded media
   - Integration with CloudFront for delivery

4. **Amazon CloudFront**
   - Content Delivery Network for static assets
   - Edge caching to improve global performance
   - HTTPS termination and SSL management

5. **AWS WAF (Web Application Firewall)**
   - Protection against common web exploits
   - Rate limiting to prevent abuse
   - Custom security rules

6. **AWS Route 53**
   - DNS management
   - Health checks and failover routing
   - Domain registration and management

7. **AWS CodePipeline**
   - CI/CD pipeline automation
   - Source integration with GitHub
   - Build and deployment stages

8. **AWS Secrets Manager**
   - Secure storage of credentials and secrets
   - Rotation of database credentials
   - Integration with ECS for secure access

9. **AWS CloudWatch**
   - Monitoring and logging
   - Alerts and notifications
   - Dashboard for system health

### Containerization

Docker is used for containerization with the following components:

1. **MediaWiki Container**
   - Core MediaWiki application
   - Custom extensions and skins
   - PHP-FPM for processing

2. **Nginx Container**
   - Web server for serving MediaWiki
   - SSL termination (if not using CloudFront)
   - Static file serving

3. **Sidecar Containers** (as needed)
   - For specific tasks like cron jobs
   - Maintenance scripts
   - Utility functions

## Network Architecture

```
                                   ┌─────────────────┐
                                   │                 │
                                   │  Route 53 DNS   │
                                   │                 │
                                   └────────┬────────┘
                                            │
                                            ▼
┌─────────────────┐             ┌─────────────────┐
│                 │             │                 │
│   CloudFront    │◄────────────│      WAF        │
│                 │             │                 │
└────────┬────────┘             └────────┬────────┘
         │                               │
         │                               │
         ▼                               ▼
┌─────────────────┐             ┌─────────────────┐
│                 │             │                 │
│   S3 Bucket     │             │ Load Balancer   │
│  (Media Files)  │             │                 │
│                 │             └────────┬────────┘
└─────────────────┘                      │
                                         │
                                         ▼
                                ┌─────────────────┐
                                │                 │
                                │   ECS Fargate   │
                                │   (MediaWiki)   │
                                │                 │
                                └────────┬────────┘
                                         │
                                         ▼
                                ┌─────────────────┐
                                │                 │
                                │   Amazon RDS    │
                                │    (MySQL)      │
                                │                 │
                                └─────────────────┘
```

## Data Flow

1. **User Request Flow**
   - User request → CloudFront → WAF → Load Balancer → ECS (MediaWiki) → RDS
   - Media requests → CloudFront → S3

2. **Content Creation Flow**
   - Admin/Editor creates content → ECS (MediaWiki) → RDS
   - Media uploads → ECS → S3 → CloudFront (for delivery)

3. **Deployment Flow**
   - Code push → GitHub → CodePipeline → Build → Test → Deploy to ECS

## Security Considerations

1. **Network Security**
   - Private subnets for database and application tiers
   - Security groups with least privilege access
   - VPC endpoints for AWS services

2. **Application Security**
   - HTTPS everywhere
   - WAF protection
   - Regular security updates
   - Input validation and sanitization

3. **Data Security**
   - Encryption at rest for RDS and S3
   - Encryption in transit (HTTPS)
   - Database backups
   - Access control for S3 objects

## Scalability and High Availability

1. **Scalability**
   - ECS auto-scaling based on CPU/memory usage
   - RDS instance scaling (vertical) as needed
   - CloudFront for edge caching

2. **High Availability**
   - Multi-AZ deployment for RDS
   - ECS tasks across multiple availability zones
   - CloudFront global edge locations

## Monitoring and Logging

1. **CloudWatch**
   - Custom metrics for MediaWiki performance
   - Logs for ECS, RDS, and other services
   - Alarms for critical thresholds

2. **Application Logging**
   - MediaWiki logs to CloudWatch
   - Error tracking and reporting
   - User activity auditing

## Disaster Recovery

1. **Backup Strategy**
   - Automated RDS backups
   - S3 versioning for media files
   - Configuration backups via CodePipeline

2. **Recovery Procedures**
   - RDS point-in-time recovery
   - ECS task replacement
   - Infrastructure recreation via CloudFormation/CDK

## Cost Optimization

1. **Resource Sizing**
   - Right-sized ECS tasks
   - RDS instance type selection
   - Auto-scaling for demand

2. **Storage Optimization**
   - S3 lifecycle policies
   - RDS storage optimization
   - CloudFront caching policies

## Future Considerations

1. **Caching Layer**
   - ElastiCache for database query caching
   - Enhanced CloudFront configurations

2. **Content Search**
   - Amazon OpenSearch Service for enhanced wiki search

3. **Localization**
   - Support for multiple languages
   - Region-specific content delivery

4. **Analytics**
   - Integration with AWS analytics services
   - User behavior tracking and analysis