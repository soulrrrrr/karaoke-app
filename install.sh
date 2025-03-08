#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Installing Karaoke App Dependencies${NC}\n"

# Check Python version
echo -e "${YELLOW}Checking Python version...${NC}"
python3 --version || { echo "Python 3.8+ is required but not installed. Aborting."; exit 1; }

# Create virtual environment
echo -e "\n${YELLOW}Creating virtual environment...${NC}"
python3 -m venv venv

# Activate virtual environment
echo -e "\n${YELLOW}Activating virtual environment...${NC}"
source venv/bin/activate

# Upgrade pip
echo -e "\n${YELLOW}Upgrading pip...${NC}"
pip install --upgrade pip

# Install basic requirements
echo -e "\n${YELLOW}Installing basic requirements...${NC}"
pip install -r requirements.txt

# Install PyTorch and torchaudio
echo -e "\n${YELLOW}Installing PyTorch and torchaudio...${NC}"
pip install torchaudio -f https://download.pytorch.org/whl/torch_stable.html

# Install latest yt-dlp
echo -e "\n${YELLOW}Installing latest yt-dlp...${NC}"
pip install -U git+https://github.com/yt-dlp/yt-dlp.git

# Check ffmpeg installation
echo -e "\n${YELLOW}Checking ffmpeg installation...${NC}"
if ! command -v ffmpeg &> /dev/null; then
    echo "ffmpeg is not installed. Please install ffmpeg manually:"
    echo "Ubuntu/Debian: sudo apt-get install ffmpeg"
    echo "macOS: brew install ffmpeg"
    echo "Windows: Download from https://www.gyan.dev/ffmpeg/builds/"
fi

echo -e "\n${GREEN}Installation complete!${NC}"
echo -e "To start the app:"
echo -e "1. Activate the virtual environment: ${YELLOW}source venv/bin/activate${NC}"
echo -e "2. Run the app: ${YELLOW}python src/app.py${NC}"