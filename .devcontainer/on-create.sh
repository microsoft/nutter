python -m pip install --upgrade pip
pip install -r requirements.txt
pip install -r dev_requirements.txt
pip install flake8
flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
flake8 . --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics
pip install pytest
pytest