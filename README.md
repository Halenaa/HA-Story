# HA-Story: AI-Powered Story Creation System

![Python Version](https://img.shields.io/badge/python-3.8%2B-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Status](https://img.shields.io/badge/status-active-brightgreen.svg)

**HA-Story** is a comprehensive AI-powered story creation system that transforms creative ideas into complete novels through a structured 5-step process. The system integrates advanced AI agents, multi-dimensional conflict detection, and intelligent quality control mechanisms to produce high-quality narrative content.

## 🌟 Key Features

### Core Story Creation Pipeline
- **📚 Outline Generation**: AI-driven story structure planning
- **👥 Character Development**: Intelligent character creation and consistency tracking
- **📖 Story Expansion**: Progressive narrative development
- **💬 Dialogue Integration**: Context-aware dialogue insertion and enhancement
- **✨ Story Enhancement**: Quality improvement and refinement

### Advanced AI Systems
- **🤖 Multi-Agent Coordination**: Specialized agents for different story aspects
- **🔍 Conflict Detection**: Multi-dimensional conflict analysis and resolution
- **🎯 Quality Control**: Automated story evaluation and improvement
- **🔄 Synchronization Engine**: Maintains consistency across all story elements
- **📊 Performance Analytics**: Comprehensive story quality metrics

### Web Interface
- **🖥️ Streamlit Web App**: User-friendly interface with ~10,000 lines of code
- **📈 Real-time Progress Tracking**: Visual progress indicators
- **🎛️ Interactive Controls**: Fine-grained parameter adjustment
- **💾 Session Management**: Save and restore creation sessions

## 🏗️ Architecture Overview

The system follows a modular 7-layer architecture:

```
🖥️ Web Interface Layer (Streamlit)
    ↓
🧠 Core Business Logic (Main Pipeline)
    ↓
🔄 Content Generation Layer (AI Agents)
    ↓
🎯 Quality Control Layer (Analysis & Evaluation)
    ↓
🔗 Synchronization Layer (State Management)
    ↓
🛠️ Utilities Layer (Tools & Helpers)
    ↓
💾 Data Layer (JSON Storage)
```

## 🚀 Quick Start

### Prerequisites
- Python 3.8 or higher
- OpenAI API key or Anthropic API key
- Required Python packages (see requirements.txt)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/Halenaa/HA-Story.git
   cd HA-Story
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**
   Create a `.env` file in the project root:
   ```env
   OPENAI_API_KEY=your_openai_api_key_here
   ANTHROPIC_API_KEY=your_anthropic_api_key_here
   ```

4. **Download language models**
   ```bash
   python -c "import spacy; spacy.cli.download('en_core_web_sm')"
   python -c "import nltk; nltk.download('punkt'); nltk.download('stopwords')"
   ```

### Running the Application

#### Web Interface (Recommended)
```bash
streamlit run outline_generator_app.py
```
Access the web interface at `http://localhost:8501`

#### Command Line Interface
```bash
python main_pipeline_glm.py --user-input "Your story idea here" --genre "fantasy"
```

## 📖 Usage Guide

### 1. Web Interface Workflow

1. **Start the Application**: Launch the Streamlit web interface
2. **Configure Settings**: Set up AI model preferences and parameters
3. **Input Story Concept**: Provide your initial story idea
4. **Follow the Pipeline**: Complete each of the 5 creation steps
5. **Review and Export**: Download your completed story

### 2. Pipeline Steps

#### Step 1: Outline Generation
- Input your story concept and genre
- AI generates a structured story outline
- Review and modify the generated outline

#### Step 2: Character Development  
- Create detailed character profiles
- Establish character relationships and conflicts
- Generate character backstories and motivations

#### Step 3: Story Expansion
- Transform outline into full narrative
- Maintain plot consistency and pacing
- Generate detailed scene descriptions

#### Step 4: Dialogue Integration
- Analyze dialogue insertion opportunities
- Generate character-appropriate dialogue
- Ensure natural conversation flow

#### Step 5: Enhancement & Polish
- Apply narrative transitions
- Improve language fluency
- Final quality control and refinement

### 3. Advanced Features

#### Multi-Agent System
The system employs specialized AI agents:
- **Dialogue Agent**: Handles conversation generation
- **Conflict Manager**: Identifies and resolves story conflicts
- **Agent Coordinator**: Manages inter-agent communication
- **Consensus Engine**: Ensures agreement between agents

#### Quality Control
- **Coherence Analysis**: Logical plot development
- **Character Consistency**: Behavioral pattern tracking
- **Emotional Development**: Natural character growth
- **Language Fluency**: Grammar and style improvement
- **Structural Completeness**: Story arc validation

## 🔧 Configuration

### Model Settings
Configure AI models in the web interface:
- **Temperature**: Controls creativity level (0.1-1.0)
- **Model Selection**: Choose between different AI providers
- **Context Length**: Adjust memory span for long stories

### Story Parameters
- **Genre**: Fantasy, Sci-Fi, Romance, Horror, etc.
- **Length**: Target word count for the final story
- **Style**: Narrative perspective and tone
- **Complexity**: Plot intricacy level

## 📊 Performance Metrics

The system includes comprehensive analytics:
- **Story Quality Scores**: Multi-dimensional evaluation
- **Coherence Metrics**: Plot consistency measurements
- **Character Development**: Growth and consistency tracking
- **Dialogue Quality**: Natural conversation assessment
- **Language Fluency**: Grammar and style evaluation

## 🧪 Experimental Features

### Human-in-the-Loop Evaluation
- Interactive story assessment interface
- Real-time feedback integration
- Quality comparison tools

### Advanced Analysis
- Semantic continuity analysis
- Emotional trajectory tracking
- Genre-specific quality metrics
- Comparative baseline analysis

## 📁 Project Structure

```
HA-Story/
├── src/                      # Core source code
│   ├── generation/           # Story generation modules
│   ├── analysis/             # Quality analysis tools
│   ├── sync/                 # Synchronization engines
│   ├── utils/                # Utility functions
│   └── evaluation/           # Evaluation systems
├── data/                     # Training data and examples
├── output/                   # Generated stories
├── scripts/                  # Utility scripts
├── storylab/                 # Experimental features
├── requirements.txt          # Python dependencies
├── main_pipeline_glm.py      # CLI interface
└── outline_generator_app.py  # Web interface
```

## 🤝 Contributing

We welcome contributions! Please see our contributing guidelines:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🔬 Research & Publications

This system has been used in academic research on AI-assisted creative writing. Key research areas include:
- Human-AI collaboration in creative processes
- Automated story quality evaluation
- Multi-agent narrative generation
- Coherence measurement in long-form text

## 📞 Support

- **Issues**: Please report bugs via GitHub Issues
- **Documentation**: Check the `/docs` folder for detailed guides
- **Community**: Join discussions in GitHub Discussions

## 🙏 Acknowledgments

- OpenAI for GPT model access
- Anthropic for Claude model support
- The open-source community for various tools and libraries
- Academic collaborators for research insights

---

**Created with ❤️ for the future of AI-assisted storytelling**
