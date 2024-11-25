cp .env.sample .env
conda env create -f environment.yml
conda activate pymol-remote
pytest tests/