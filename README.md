# Ditto TalkingHead Docker Container

This repository contains a Docker setup for the [ditto-talkinghead](https://github.com/antgroup/ditto-talkinghead) project, which provides Motion-Space Diffusion for Controllable Realtime Talking Head Synthesis.

## Prerequisites

- Docker with GPU support
- NVIDIA Docker runtime
- NVIDIA GPU with CUDA support
- Docker Compose (optional but recommended)

## Quick Start

### Remote Deployment (Recommended)

For deploying on another server, use the setup script:

```bash
# Clone with submodules
git clone --recursive https://github.com/your-username/ditto-container.git
cd ditto-container

# Run setup script (handles submodules + Docker build + run)
./setup.sh

# Or step by step:
./setup.sh setup  # Setup submodules
./setup.sh build  # Build Docker image  
./setup.sh run    # Run container
```

### Using Docker Compose (Local Development)

1. **Build and run the container:**
   ```bash
   docker-compose up -d --build
   ```

2. **Access the container:**
   ```bash
   docker-compose exec ditto-talkinghead bash
   ```

3. **Stop the container:**
   ```bash
   docker-compose down
   ```

### Using Docker directly

1. **Build the image (includes source code):**
   ```bash
   docker build -t ditto-talkinghead .
   ```

2. **Run the container:**
   ```bash
   docker run -it --gpus all \
     -v $(pwd)/checkpoints:/app/checkpoints \
     -v $(pwd)/data:/app/data \
     -v $(pwd)/output:/app/output \
     -p 8000:8000 \
     --name ditto-container \
     ditto-talkinghead
   ```

   Note: When using Docker directly, the source code from the `src/` submodule is built into the container at `/app/src/`.

## Container Features

- **Base Image:** NVIDIA CUDA 11.8 with Ubuntu 22.04 + manually installed cuDNN8
- **Python:** 3.10
- **GPU Support:** Full CUDA and TensorRT support
- **Pre-installed Tools:** git-lfs, vim
- **Source Code:** 
  - Docker Compose: Mounted from local `./src` directory (development mode)
  - Docker Direct: Built into container at `/app/src/` (deployment mode)
- **Pre-installed Dependencies:**
  - PyTorch with CUDA support
  - TensorRT 8.6.1
  - OpenCV
  - librosa
  - All other required packages from the original repository

## Directory Structure

### For Docker Compose (Development Mode)
Volume mounts for live development:
```
./
├── src/                 # Git submodule: mounted to /app/src in container
├── checkpoints/          # Model checkpoints: mounted to /app/checkpoints
├── data/                # Input data: mounted to /app/data
├── output/              # Generated outputs: mounted to /app/output
└── docker files...
```

### For Direct Docker (Deployment Mode)
Only external data needs to be mounted:
```
./
├── src/                 # Git submodule: built into container at /app/src
├── checkpoints/          # Model checkpoints: mounted to /app/checkpoints  
├── data/                # Input data: mounted to /app/data
├── output/              # Generated outputs: mounted to /app/output
└── docker files...
```

The source code is managed as a git submodule from https://github.com/fciannella/ditto-talkinghead.

## Setting Up the Project

After running the container, you'll need to:

1. **Download the model checkpoints:**
   ```bash
   cd /app
   git lfs install
   git clone https://huggingface.co/digital-avatar/ditto-talkinghead checkpoints
   ```

2. **Run inference:**
   ```bash
   cd /app/src
   python inference.py \
     --data_root "/app/checkpoints/ditto_trt_Ampere_Plus" \
     --cfg_pkl "/app/checkpoints/ditto_cfg/v0.4_hubert_cfg_trt.pkl" \
     --audio_path "/app/data/audio.wav" \
     --source_path "/app/data/image.png" \
     --output_path "/app/output/result.mp4"
   ```

   The source code from your fork is available in `/app/src` and any changes you make locally will be reflected in the container.

## 🎥 Real-time Streaming Services

In addition to batch processing, this container includes **real-time streaming services** for live talking head generation:

### 🌐 WebSocket Service
```bash
# Inside container
cd /app/src
python websocket_server.py

# Open browser with your server's IP/hostname:
# http://YOUR_SERVER_IP:8000  (for remote server)
# http://localhost:8000       (for local development)
# Built-in web interface - no separate client needed!
```

⚠️ **Notes:** 
- Make sure to put a source image (avatar photo) at `/app/data/source_image.png` 
- For remote servers, replace `YOUR_SERVER_IP` with your actual server IP or hostname
- The WebSocket URL is automatically detected from the browser location

**See `websocket_server.py` for a simple FastAPI based implementation.**

## Working with the Git Submodule

The `src/` directory is a git submodule pointing to your fork. To work with it:

```bash
# Update the submodule to latest from your fork
git submodule update --remote src

# Make changes to the code in ./src/
# Then commit and push from within the src directory
cd src
git add .
git commit -m "Your changes"
git push origin main

# Update the main repository to point to the new commit
cd ..
git add src
git commit -m "Update submodule"
git push
```

## 🚀 Remote Deployment & Submodules

### For Remote Servers:

1. **Clone with submodules:**
```bash
git clone --recursive https://github.com/your-username/ditto-container.git
```

2. **Use the setup script:**
```bash
cd ditto-container
./setup.sh  # Handles everything automatically
```

### Submodule Troubleshooting:

**If src/ directory is empty after cloning:**
```bash
git submodule update --init --recursive
```

**If submodule is out of date:**
```bash
git submodule update --remote --recursive
```

**To update submodule to latest commit:**
```bash
cd src
git pull origin main
cd ..
git add src
git commit -m "Update submodule to latest"
```

## GPU Compatibility

The pre-built TensorRT models are compatible with `Ampere_Plus` GPUs. If your GPU doesn't support this, you'll need to convert the ONNX models to TensorRT inside the container:

```bash
cd /app/src
python scripts/cvt_onnx_to_trt.py \
  --onnx_dir "/app/checkpoints/ditto_onnx" \
  --trt_dir "/app/checkpoints/ditto_trt_custom"
```

Then use `--data_root=/app/checkpoints/ditto_trt_custom` in your inference command.

## Troubleshooting

### GPU Not Detected
Ensure you have:
- NVIDIA drivers installed on the host
- NVIDIA Docker runtime installed
- Used `--gpus all` flag or proper docker-compose GPU configuration

### Permission Issues
The container runs as a non-root user. If you encounter permission issues with mounted volumes, adjust the ownership:
```bash
sudo chown -R 1000:1000 ./checkpoints ./data ./output ./src
```

### Memory Issues
This model requires significant GPU memory. Ensure your GPU has enough VRAM (recommended: 8GB+).

### cuDNN Library Issues
If you get errors about missing `libcudnn.so.8`, this should be resolved as the Dockerfile installs cuDNN8 manually via apt packages (`libcudnn8` and `libcudnn8-dev`).


## Run on OCI

## Push the container to gitlab

```
docker build -t gitlab-master.nvidia.com/fciannella/ditto-container/ditto-container:0.0.1 -t gitlab-master.nvidia.com/fciannella/ditto-container/ditto-container:latest .
docker push gitlab-master.nvidia.com/fciannella/ditto-container/ditto-container:0.0.1
docker push gitlab-master.nvidia.com/fciannella/ditto-container/ditto-container:latest
```

## Run the container on OCI

```
srun -A llmservice_nemo_mlops -p interactive_singlenode -G 4 --time 04:00:00 --container-mounts /lustre/fsw/portfolios/llmservice/users/fciannella/cache:/root/.cache,/lustre/fsw/portfolios/llmservice/users/fciannella/src:/root/src --container-image gitlab-master.nvidia.com/fciannella/ditto-container/ditto-container:latest --pty bash
```


## Test the inference

```
python inference.py \
    --data_root "./checkpoints/ditto_trt_Ampere_Plus" \
    --cfg_pkl "./checkpoints/ditto_cfg/v0.4_hubert_cfg_trt.pkl" \
    --audio_path "./tmpcc1gbdw3.wav" \
    --source_path "./chris_avatar.png" \
    --output_path "./result.mp4" 
```


## License

This Docker setup is provided under the same Apache-2.0 license as the original ditto-talkinghead project. 





export TMPDIR=/root/src/.cache
export TEMP=/root/src/.cache
export TMP=/root/src/.cache
export PYXBLD_DIR=/root/src/.cache/pyxbld
mkdir -p /root/src/.cache/pyxbld

# Clean up any existing build cache
rm -rf /root/.pyxbld/