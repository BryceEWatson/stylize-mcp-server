# Contributing to Stylize MCP Server

Thank you for your interest in contributing to the Stylize MCP Server! This document provides guidelines and instructions for contributors.

## 🚀 Quick Start for Contributors

1. **Fork the repository**
2. **Clone your fork**: `git clone https://github.com/your-username/stylize-mcp.git`
3. **Set up development environment**: See [Development Setup](#development-setup)
4. **Create a feature branch**: `git checkout -b feature/amazing-feature`
5. **Make your changes and add tests**
6. **Run tests**: `pytest`
7. **Submit a pull request**

## Development Setup

### Prerequisites
- Python 3.10 or newer
- Google Cloud SDK (for local development)
- OpenAI API key (for testing)

### Environment Setup
```bash
# Clone and enter the project
git clone https://github.com/your-username/stylize-mcp.git
cd stylize-mcp

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install development dependencies
pip install pytest-cov ruff black isort

# Set up environment variables for development
export OPENAI_API_KEY=your_openai_api_key_here
export GCP_PROJECT_ID=your_test_project_id
export AUTH_DEV_BYPASS=true
export DEV_API_KEY=test-dev-key

# Run tests to verify setup
pytest
```

## Code Style and Quality

We maintain high code quality standards:

### Formatting
```bash
# Format code with black
black app/ tests/

# Sort imports with isort  
isort app/ tests/

# Lint with ruff
ruff check app/ tests/

# Auto-fix linting issues
ruff check --fix app/ tests/
```

### Testing
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_main.py

# Run tests in parallel
pytest -n auto
```

## Project Structure

```
stylize-mcp/
├── app/                    # Main application code
│   ├── main.py            # FastAPI application entry point
│   ├── models.py          # Pydantic models
│   ├── *_service.py       # Service layer modules
│   └── styles.json        # Style definitions
├── tests/                 # Test suite
├── infra/                 # Terraform infrastructure
├── docs/                  # Documentation
└── .github/workflows/     # CI/CD pipelines
```

## Types of Contributions

### 🐛 Bug Reports
When reporting bugs, please include:
- Clear description of the issue
- Steps to reproduce
- Expected vs actual behavior
- Environment details (Python version, OS, etc.)
- Relevant logs or error messages

### ✨ Feature Requests
For new features:
- Check existing issues first
- Describe the use case clearly
- Consider backwards compatibility
- Propose implementation approach if possible

### 🔧 Code Contributions

#### Areas for Contribution

**High Priority:**
- **New Art Styles**: Add styles to `app/styles.json` with prompts
- **Performance Optimizations**: Caching, response times, memory usage
- **API Enhancements**: New endpoints, improved error handling
- **Documentation**: Tutorials, examples, API docs

**Medium Priority:**
- **MCP Tools**: Additional Model Context Protocol integrations  
- **Authentication**: OAuth providers, SSO integration
- **Monitoring**: Better observability and metrics
- **Testing**: Edge cases, integration tests

**Low Priority:**
- **UI/Frontend**: Admin dashboard, user portal
- **Deployment**: Alternative cloud providers, Kubernetes
- **Integrations**: Webhooks, third-party services

### 📝 Documentation
- API documentation improvements
- Tutorial creation
- Code comments and docstrings
- README enhancements

## Coding Guidelines

### Python Style
- Follow PEP 8 (enforced by ruff)
- Use type hints where applicable
- Write descriptive docstrings for public functions
- Keep functions focused and small

### API Design
- Follow REST conventions
- Use appropriate HTTP status codes
- Include comprehensive error messages
- Maintain backwards compatibility

### Testing
- Write tests for new features
- Maintain or improve test coverage
- Use descriptive test names
- Include both positive and negative test cases

### Example Test Structure
```python
def test_stylize_image_success(test_client, valid_image):
    """Test successful image stylization with valid inputs."""
    response = test_client.post(
        "/stylize_image",
        files={"image": ("test.jpg", valid_image, "image/jpeg")},
        data={"style_id": "van_gogh"}
    )
    assert response.status_code == 200
    assert "stylized_image_url" in response.json()
```

## Pull Request Process

### Before Submitting
1. **Run the full test suite**: `pytest`
2. **Check code formatting**: `black app/ tests/ && isort app/ tests/`
3. **Run linting**: `ruff check app/ tests/`
4. **Update documentation** if needed
5. **Add tests** for new functionality

### PR Guidelines
- **Clear title**: Describe what the PR accomplishes
- **Detailed description**: Explain the changes and why they're needed
- **Link related issues**: Use "Fixes #123" or "Addresses #456"
- **Small, focused changes**: Avoid large, multi-purpose PRs
- **Update CHANGELOG**: Add entry for significant changes

### Review Process
1. **Automated checks**: CI must pass (tests, linting, security)
2. **Code review**: Maintainer review for code quality and design
3. **Testing**: Verify functionality works as expected
4. **Documentation**: Ensure docs are updated appropriately

## Style Guide Examples

### Adding a New Art Style
```json
// In app/styles.json
{
  "id": "my_new_style",
  "name": "My New Style",
  "description": "Description of the artistic style and its characteristics",
  "prompt_fragment": "detailed prompt template for DALL-E 3"
}
```

### Adding a New API Endpoint
```python
@app.post("/my_endpoint")
async def my_endpoint(
    request: MyRequestModel,
    service: MyService = Depends(get_my_service)
) -> MyResponseModel:
    """
    Brief description of what this endpoint does.
    
    Args:
        request: Description of request parameters
        service: Injected service dependency
        
    Returns:
        MyResponseModel: Description of response
        
    Raises:
        HTTPException: When and why this might be raised
    """
    try:
        result = await service.do_something(request)
        return MyResponseModel(**result)
    except ServiceError as e:
        raise HTTPException(status_code=400, detail=str(e))
```

## Security Considerations

- **Never commit secrets** (API keys, passwords, tokens)
- **Validate all inputs** thoroughly
- **Use parameterized queries** for database operations
- **Follow OWASP guidelines** for web security
- **Report security issues privately** to maintainers

## Performance Guidelines

- **Use async/await** for I/O operations
- **Implement caching** for expensive operations
- **Monitor resource usage** (memory, CPU, network)
- **Optimize database queries** and API calls
- **Use connection pooling** for external services

## Getting Help

- **GitHub Issues**: For bugs and feature requests
- **GitHub Discussions**: For questions and general discussion
- **Documentation**: Check existing docs first
- **Code Comments**: Look for implementation details

## Recognition

Contributors will be recognized in:
- CONTRIBUTORS.md file
- GitHub contributors page
- Release notes for significant contributions

## License

By contributing, you agree that your contributions will be licensed under the same license as the project (MIT License).

---

**Happy Contributing! 🎨✨**

Together, we're building an amazing tool for AI-powered image generation and stylization!