# Wiki7 Infrastructure (CDK Project)

This project defines the AWS infrastructure for the **Wiki7 MediaWiki site** using the AWS Cloud Development Kit (CDK) in TypeScript.

---

## Project Structure

```plaintext
wiki7-cdk/
├── bin/
│   └── wiki7.ts                # CDK App entry point
├── lib/
│   ├── wiki7-cdk-stack.ts       # Master stack orchestrating the components
│   ├── network-stack.ts         # VPC and Security Groups
│   ├── database-stack.ts        # Secrets Manager and RDS database
│   └── application-stack.ts     # ECS Cluster, Fargate Service, Load Balancer
├── cdk.json
├── package.json
└── tsconfig.json
