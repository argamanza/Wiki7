# 📘 Wiki7 Project Roadmap

A structured plan for building the Hapoel Beer Sheva fan wiki on MediaWiki using AWS-managed infrastructure and modern DevOps practices.

---

## ✅ Project Objectives
Your Wiki7 project aims to create a fan-driven wiki for Hapoel Beer Sheva FC, with:

- [x] **MediaWiki** as the content platform
- [x] **Modern AWS-managed infrastructure** for scalability and performance
- [x] **CI/CD pipeline** to enable smooth and automated staging and production deployments
- [x] **Custom design** inspired by Maccabipedia and Wikipoel, to capture the spirit of the club and community

---

## 🔧 Technical Stack

### Core Components
- [x] **MediaWiki** – Core content engine
- [x] **Docker** – Enables containerized, reproducible dev/prod environments
- [x] **AWS ECS** (Elastic Container Service) – Manages container orchestration via Fargate or EC2
- [x] **AWS RDS (PostgreSQL)** – Scalable managed database with built-in backups and monitoring
- [x] **AWS S3** – For uploading and serving images and file media
- [x] **AWS CloudFront** – Global CDN for caching and fast delivery
- [x] **GitHub** – Source control and collaboration hub
- [x] **AWS CodePipeline/CodeBuild** – CI/CD for automated builds and deployments
- [x] **AWS CloudFormation/CDK** – Infrastructure as Code using developer-friendly tools
- [x] **AWS Route 53** – DNS and domain management for the wiki

### Why This Stack
- [x] **Containerization**: Ensures parity across environments and smooth deployments
- [x] **Managed AWS Services**: Reduces operational overhead without losing control
- [x] **PostgreSQL**: More performant than MySQL for high-traffic wikis with many edits and queries
- [x] **CodePipeline**: Seamless native integration with other AWS services
- [x] **CDK**: Allows you to define infrastructure using familiar programming languages

---

## 📆 Project Phases and Checklist

### Phase 1: Environment Setup & Planning
- [x] Set up initial GitHub repository with clear directory structure
- [x] Create a minimal Docker setup for local MediaWiki development
- [x] Design initial AWS infrastructure diagram (VPC, RDS, ECS, S3, Route 53, etc.)
- [x] Manually deploy a basic version of each core service to understand configurations and needs

### Phase 2: Infrastructure as Code (IaC)
- [ ] Build CDK templates for core services: VPC, RDS, ECS services, S3 buckets, CloudFront distribution
- [ ] Configure private/public subnets, routing tables, and internet gateways in VPC
- [ ] Deploy PostgreSQL database using RDS with proper subnet groups and security groups
- [ ] Define ECS task definitions and service for MediaWiki Docker container

### Phase 3: CI/CD Pipeline
- [ ] Define CodePipeline with separate staging and production stages
- [ ] Use CodeBuild to build Docker images and push to Amazon ECR
- [ ] Add automated validation (e.g. health checks, linting, extension tests)
- [ ] Include manual approval gates for production deployments, and support for rollbacks

### Phase 4: MediaWiki Customization
- [ ] Install essential MediaWiki extensions (ParserFunctions, VisualEditor, etc.)
- [ ] Customize UI/theme to align with Maccabipedia / Wikipoel visual style
- [ ] Design content structure: player pages, season summaries, match histories, fan chants/tifos
- [ ] Secure the platform with CAPTCHA, user permission tiers, and abuse filters

### Phase 5: Content & Launch
- [ ] Create and import seed content (history, players, titles, managers)
- [ ] Set up structured media management workflows (categories, galleries, etc.)
- [ ] Perform load tests and performance audits with CloudWatch monitoring
- [ ] Launch production version, enable domain via Route 53, and begin post-launch monitoring

---

## 🎓 Learning & Execution Approach
Each phase follows this cycle:

- **Learn** → Research the relevant technologies and practices for the phase
- **Plan** → Create implementation and architecture diagrams
- **Execute** → Build the feature or component in small, manageable chunks
- **Review** → Test, validate, and iterate on what has been built

---

## 🔜 Immediate Next Steps
- [ ] Create GitHub repository structure (e.g. `docker/`, `infrastructure/`, `mediawiki/`, `docs/`)
- [ ] Set up local MediaWiki development with Docker Compose
- [ ] Build basic MediaWiki image or use existing official image
- [ ] Begin planning AWS architecture with diagrams for VPC, ECS, RDS, S3, and CloudFront

