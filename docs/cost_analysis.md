# Cost Analysis: Shopify Size Chart Extractor Service

## Executive Summary

This document provides a comprehensive cost analysis for running the Shopify Size Chart Extractor service at scale. The analysis includes all major cost components: infrastructure, Gemini API usage, browser automation, and operational expenses. The service uses a hybrid approach combining HTML parsing, Selenium automation, and Gemini 2.5 Flash API for image-based size chart extraction.

## Service Architecture Overview

The service employs different extraction strategies based on the store:

- **HTML Parsing**: Westside (direct HTML table extraction)
- **Selenium + HTML Parsing**: LittleBoxIndia (JavaScript-rendered content)
- **Selenium + Gemini API**: Freakins, Squah (image-based size charts)

## Key Assumptions

- Average of 100 products with size charts per store
- Extraction runs once per month
- Average product page size: 150KB
- Average size chart image: 200KB
- ~50% of stores require Gemini API (image-based extraction)
- ~75% of stores require Selenium (JavaScript rendering)
- Rate limit: 1 request per second per store
- Cloud deployment on AWS/GCP

## Gemini 2.5 Flash API Pricing

Based on the latest pricing updates and our specific usage profile:

- **Input (images)**: $0.30 per 1M tokens
- **Output**: $2.50 per 1M tokens
- **Average tokens per image**: ~800 input + ~300 output (total ~1,100 tokens)
- **Cost per image extraction**: ~$0.00099 (calculated as (800/1M)*$0.30 + (300/1M)*$2.50)

*Note: Gemini 2.5 Flash no longer has a separate "thinking" vs. "non-thinking" price, simplifying cost calculations. This update reflects the stable version pricing as of June 17, 2025.* [https://developers.googleblog.com/en/gemini-2-5-thinking-model-updates/](https://developers.googleblog.com/en/gemini-2-5-thinking-model-updates/)

## Detailed Cost Projections

### 1,000 Stores (Monthly)

**Data Processing Volume:**

- Total products to process: 100,000
- Products requiring Gemini API: ~50,000
- HTTP requests: ~120,000 (including retries)
- Selenium browser sessions: ~75,000
- Data transfer: ~25GB

**Cost Breakdown:**

1.  **Gemini API Costs**: $49.50

    -   50,000 image extractions × $0.00099 = $49.50

2.  **Compute Infrastructure**: $80-120

    -   EC2 t3.large (8GB RAM, 2 vCPU) for main processing
    -   Additional instance for Selenium Chrome browsers
    -   Run time: ~40 hours/month

3.  **Selenium/Chrome Resources**: $30

    -   Headless Chrome instances
    -   Additional memory overhead

4.  **Storage**: $8

    -   JSON output: ~1GB
    -   Logs: ~5GB
    -   Temporary browser cache: ~10GB

5.  **Data Transfer**: $3

    -   Egress charges for ~25GB

6.  **Monitoring/Logging**: $15

**Total Monthly Cost: $185.50 - $225.50**
**Cost per store: $0.19 - $0.23**


### 100,000 Stores (Monthly)

**Data Processing Volume:**

- Total products: 10,000,000
- Products requiring Gemini API: ~5,000,000
- HTTP requests: ~12,000,000
- Selenium browser sessions: ~7,500,000
- Data transfer: ~2.5TB

**Cost Breakdown:**

1.  **Gemini API Costs**: $4,950

    -   5,000,000 image extractions × $0.00099 = $4,950

2.  **Compute Infrastructure**: $3,000-4,000

    -   Kubernetes cluster with 15-25 nodes
    -   Auto-scaling based on load
    -   Run time: ~4,000 hours distributed

3.  **Selenium Grid at Scale**: $1,500

    -   Distributed Selenium Grid
    -   100+ concurrent browser instances
    -   Dedicated node pool for browsers

4.  **Storage**: $300

    -   JSON output: ~100GB
    -   Logs: ~500GB (compressed)
    -   Browser cache: ~1TB (ephemeral)

5.  **Data Transfer**: $300

    -   Egress charges for ~2.5TB

6.  **Database Cluster**: $300

    -   Managed PostgreSQL with read replicas

7.  **Queue/Streaming Service**: $200

    -   Kafka or managed queue service

8.  **CDN/Proxy Service**: $800

    -   IP rotation service
    -   Request distribution

9.  **Monitoring/Observability**: $500
    -   Full APM and logging stack
    -   Custom metrics and alerting

**Total Monthly Cost: $10,850 - $11,850**
**Cost per store: $0.11 - $0.12**

## Primary Cost Drivers

### 1. **Gemini API Costs (30-50% at scale)**

- Linear scaling with image-based extractions
- Significant portion of total cost
- No volume discounts in free tier

### 2. **Compute Resources (25-35%)**

- Browser automation overhead
- Concurrent processing requirements
- Memory-intensive Chrome instances

### 3. **Selenium/Browser Infrastructure (10-15%)**

- Headless Chrome resource usage
- Grid management at scale
- Browser process isolation

### 4. **Data Transfer & Storage (5-10%)**

- Image downloads for Gemini
- HTML page downloads
- Result storage

### 5. **Supporting Services (10-15%)**

- Database for job management
- Queue services
- Monitoring and logging

## Cost Optimization Strategies

### 1. **Gemini API Optimization**

**Intelligent Image Detection**

- Pre-filter products likely to have image-based charts
- Implement image classification before Gemini calls
- **Potential savings: 20-30% on API costs**

**Use OCR Model Instead of Gemini API**

**Image Preprocessing**

- Compress images before sending to Gemini
- Crop to relevant sections
- **Potential savings: 10-15% on API costs**

**Caching Gemini Results**

- Cache extracted size charts
- Detect unchanged products
- **Potential savings: 30-40% on repeat extractions**

### 2. **Infrastructure Optimization**

**Hybrid Extraction Strategy**

- Route stores to appropriate extractors
- Avoid Selenium when not needed
- **Potential savings: 25-35% on compute**

**Serverless for Gemini Processing**

- Use Lambda/Cloud Functions for image extraction
- Pay only for processing time
- **Potential savings: 20-30% on compute**

**Browser Pool Management**

- Reuse browser instances
- Implement efficient queue system
- **Potential savings: 15-20% on resources**

### 3. **Architectural Improvements**

**Store Classification System**

```python
# Classify stores by extraction method needed
STORE_CLASSIFICATIONS = {
    'html_only': ['westside.com'],  # No Selenium, No Gemini
    'selenium_only': ['littleboxindia.com'],  # Selenium, No Gemini
    'selenium_gemini': ['freakins.com', 'squah.com']  # Both needed
}
```

**Tiered Processing Pipeline**

1. Try HTML extraction first (cheapest)
2. Fall back to Selenium if needed
3. Use Gemini only for image-based charts

**Potential savings: 40-50% overall**

### 4. **Scale-Specific Optimizations**

**For 1,000 Stores:**

- Single instance with job queue
- Local Chrome instance
- Batch Gemini API calls
- **Optimized cost: $150-180/month**

**For 10,000 Stores:**

- Containerized deployment
- Selenium Grid with 5-10 browsers
- Implement Gemini result caching
- **Optimized cost: $1,000-1,200/month**

**For 100,000 Stores:**

- Kubernetes with node pools
- Distributed Selenium Grid
- Gemini request batching
- Multi-region deployment
- **Optimized cost: $8,000-9,000/month**

## Recommended Architecture by Scale

### Small Scale (< 1,000 stores)

```yaml
Single Instance Architecture:
  - EC2/GCE instance (t3.large)
  - Local Chrome browser
  - SQLite job queue
  - Direct Gemini API calls
  - Basic CloudWatch monitoring
```

### Medium Scale (1,000-10,000 stores)

```yaml
Distributed Architecture:
  - Auto-scaling group (3-5 instances)
  - Selenium Grid (Docker Swarm)
  - PostgreSQL RDS
  - SQS for job queue
  - Gemini API with retry logic
  - ElastiCache for result caching
```

### Large Scale (> 10,000 stores)

```yaml
Kubernetes Architecture:
  - Multi-node K8s cluster
  - Distributed Selenium Grid
  - PostgreSQL cluster with read replicas
  - Kafka for job streaming
  - Gemini API with request pooling
  - Redis cluster for caching
  - Prometheus + Grafana monitoring
```

## Cost Comparison with Alternatives

### Manual Extraction

- Human cost: ~$0.50-1.00 per store
- Time: 5-10 minutes per store
- Our service: $0.12-0.24 per store (automated)

### Competing Services

- Web scraping APIs: $0.30-0.50 per store
- Full-service extraction: $1.00-2.00 per store
- Our service provides better value with Gemini integration


## Risk Mitigation

### API Rate Limits

- Implement exponential backoff
- Distribute requests across time
- Use multiple API keys if needed

### Cost Overruns

- Set up billing alerts
- Implement cost caps
- Regular usage monitoring

### Service Reliability

- Implement circuit breakers
- Graceful degradation
- Fallback extraction methods

## Conclusion

The Shopify Size Chart Extractor service can operate cost-effectively at all scales with proper architecture and optimization. The inclusion of Gemini API adds significant capability for image-based extraction but requires careful cost management.

**Key Takeaways:**

1. **Gemini API is the largest cost driver** but provides essential functionality
2. **Hybrid approach** (HTML + Selenium + Gemini) optimizes costs
3. **Caching and intelligent routing** can reduce costs by 40-50%
4. **Costs scale sub-linearly** with proper optimization

**Final Cost Summary (Optimized):**

- **1,000 stores**: $0.15-0.18 per store
- **10,000 stores**: $0.10-0.12 per store
- **100,000 stores**: $0.08-0.09 per store

This demonstrates strong economies of scale while maintaining high-quality extraction capabilities across diverse store implementations.
