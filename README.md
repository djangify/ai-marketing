# AI Marketing Platform

## Overview

The AI Marketing Platform is a Django-based web application designed to streamline content creation and repurposing for marketers. By leveraging artificial intelligence, the platform allows users to transform existing content assets into various marketing formats while maintaining their authentic voice and brand identity.

Rather than replacing human creativity, the platform enhances it by handling the time-consuming aspects of content transformation, allowing marketers to produce more high-quality content in less time.

## Core Value Proposition

- **Content Transformation**: Turn one piece of content into multiple formats
- **Time Efficiency**: Save hours on content repurposing
- **Maintain Authenticity**: Preserve your unique voice while scaling content output
- **Cross-Channel Optimization**: Generate platform-specific content for various marketing channels

## Technical Stack

- **Backend**: Django web framework with MariaDB
- **Frontend**: Tailwind CSS for styling with HTMX for dynamic interactions
- **AI Integration**: OpenAI API for content generation
- **Deployment**: VPS hosting environment

## Application Structure

The platform consists of several interconnected Django apps, each with specific functionality:

### 1. Projects App

The Projects app serves as the container for organizing all content creation activities. Each project encapsulates assets, prompts, and generated content.

**Key Models:**

- `Project`: Contains basic project information, user association, and keywords
- `GeneratedContent`: Stores AI-generated content results

**Main Features:**

- Project creation and management
- Tagging system for organization
- Integrated workflow between assets, prompts, and generated content

### 2. Assets App

The Assets app handles the uploading, processing, and management of source content files that serve as the foundation for AI-powered content generation.

**Key Models:**

- `Asset`: Stores metadata about uploaded files including token counts
- `AssetProcessingJob`: Manages background processing of uploaded assets

**Supported File Types:**

- Text files (.txt)
- Markdown (.md)
- PDF documents
- Audio files (for transcription)
- Video files (for transcription)

**Features:**

- Drag-and-drop file uploads
- Automatic content extraction and tokenization
- Token usage tracking for subscription limits

### 3. Prompts App

The Prompts app allows users to create custom instructions that guide how the AI generates content from their assets.

**Key Models:**

- `Prompt`: Stores prompt text, token count, and order within a project

**Features:**

- Custom prompt creation
- Template import functionality
- Token usage tracking
- Ordering system for multi-step content generation

### 4. Content Templates App

The Content Templates app enables users to save collections of prompts as reusable templates for consistent content generation.

**Key Models:**

- `Template`: Contains template metadata and user association
- `TemplatePrompt`: Stores individual prompts within a template

**Features:**

- Template creation and management
- Prompt organization within templates
- Template sharing (for organizational users)

### 5. Content Generation App

The Content Generation app handles the AI-powered transformation of assets using prompts to create marketing content.

**Key Models:**

- `ContentGenerationJob`: Tracks the progress of generation tasks
- `AIConfig`: Stores configuration settings for OpenAI integration
- `PromptTemplate`: System-level prompt templates for different content types

**Features:**

- Background processing of content generation requests
- Progress tracking and job management
- Advanced prompt enhancement through layering
- DOCX and batch export capabilities

### 6. Prompt Generator App

The Prompt Generator app provides guided templates for creating effective prompts without requiring expertise in prompt engineering.

**Key Models:**

- `GeneratorCategory`: Categories for different prompt templates
- `GeneratorTemplate`: Template structures for prompt creation
- `GeneratorParameter`: Configurable parameters within templates
- `GeneratedPrompt`: User-generated prompts from templates

**Features:**

- Category-based template browsing
- Fill-in-the-blank prompt generation
- Parameter customization
- Direct export to projects

### 7. SEO Optimization App

The SEO Optimization app analyzes generated content and provides recommendations for search engine optimization.

**Key Models:**

- `SEOAnalysis`: Stores analysis results for generated content
- `KeywordTracking`: Tracks and manages keywords across projects

**Features:**

- Readability scoring (Flesch Reading Ease)
- Keyword density analysis
- Meta description generation and editing
- SEO score calculation and improvement suggestions

### 8. Accounts App

The Accounts app manages user authentication, profiles, and member resources.

**Key Models:**

- `Profile`: Extended user profile information
- `TokenUsage`: Tracks token consumption for subscription limits
- `MemberResource`: Educational content for platform users

**Features:**

- User registration and authentication
- Profile management
- Token usage tracking across platform
- Access to exclusive member resources

### 9. Subscriptions App

The Subscriptions app handles billing, payment processing, and access control via Stripe integration.

**Key Models:**

- `Subscription`: Tracks subscription status and details
- `UserProfile`: Manages trial periods and subscription-related user data

**Features:**

- Stripe payment processing
- Trial period management
- Subscription level enforcement
- Token usage limits based on subscription tier

## Key Technical Components

### Prompt Layering System

One of the platform's core strengths is its sophisticated prompt layering system that ensures high-quality AI-generated content:

1. **Base Layer**: System prompts that establish fundamental content guidelines
2. **Content Type Layer**: Specialized instructions for specific content formats (blog posts, social media, emails)
3. **User Prompt Layer**: Custom user instructions that guide the AI
4. **Asset Content Layer**: Source material information extracted from uploaded files

This layered approach produces more contextually relevant and higher-quality output than basic prompting.

### Token Management System

The platform implements a comprehensive token tracking system to:

1. Monitor usage across the platform
2. Enforce subscription-based limits
3. Reset counters on subscription renewal
4. Provide usage statistics to users

### Background Processing

To handle resource-intensive operations without blocking the user interface, the platform employs background processing for:

1. Asset content extraction and tokenization
2. AI-powered content generation
3. SEO analysis

## Installation and Setup

### Prerequisites

- Python 3.10+
- PostgreSQL database
- Node.js 17 (for Tailwind CSS)
- VPS hosting environment

### Environment Variables

The following environment variables need to be configured:

```
SECRET_KEY=your_django_secret_key
DEBUG=False
DATABASE_NAME=your_db_name
DATABASE_USER=your_db_user
DATABASE_PASSWORD=your_db_password
DATABASE_HOST=localhost
DATABASE_PORT=3306
OPENAI_API_KEY=your_openai_api_key
STRIPE_PUBLISHABLE_KEY=your_stripe_publishable_key
STRIPE_SECRET_KEY=your_stripe_secret_key
STRIPE_WEBHOOK_SECRET=your_stripe_webhook_secret
```

### Installation Steps

1. Clone the repository
2. Install Python dependencies: `pip install -r requirements.txt`
3. Install NLTK data for SEO analysis: `python -m nltk.downloader punkt stopwords`
4. Configure environment variables
5. Run migrations: `python manage.py migrate`
6. Create default data:
   - `python manage.py create_default_ai_config`
   - `python manage.py create_default_templates`
   - `python manage.py import_templates path/to/templates.json`
7. Collect static files: `python manage.py collectstatic`
8. Create a superuser: `python manage.py createsuperuser`
9. Start the server: `python manage.py runserver`

## Usage Workflow

### Typical User Journey

1. **Create a Project**: Set up a new project with a title and relevant keywords
2. **Upload Assets**: Add content files (text, PDFs, audio, video) to the project
3. **Create/Import Prompts**: Build custom prompts or import from templates
4. **Generate Content**: Use the AI to transform assets based on prompts
5. **Analyze and Optimize**: Review SEO analysis and make improvements
6. **Export and Use**: Download generated content for use in marketing campaigns

## Future Development Roadmap

- Enhanced media processing capabilities
- Additional language support
- Integration with popular marketing platforms
- Advanced analytics dashboard
- Custom training for company-specific voice and style

## Contributing

Contributions to the AI Marketing Platform are welcome. Please follow these steps:

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Commit your changes: `git commit -m 'Add some feature'`
4. Push to the branch: `git push origin feature-name`
5. Submit a pull request

## Contact

Diane Corriette
https://www.djangify.com
