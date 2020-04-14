[![Documentation Status](https://readthedocs.org/projects/covid19-data-analyzer/badge/?version=latest)](https://covid19-data-analyzer.readthedocs.io/en/latest/?badge=latest)
[![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/s-weigand/covid19-data-analyzer/master?urlpath=lab%2Ftree%2Fdev_nb.ipynb)

# covid19-data-analyzer

Especially in times of crisis and panic, with many different opinions on the topic, people should try to derive their own conclusion.
Luckily we live in a time, where the skills and tools to analyse data are open to everyone.
Thus this little project tries to provide you with the data and a small toolset
to understand, what the current state of the covid19 pandemic is right now.

The code of this repository is the basis for [istcoronaexponentiell.de](https://vm-1.istcoronaexponentiell.de/),
where this projects interactive dashboard is hosted.

# Usage

1. Clone or download this repository

2. Install the dependencies

   ```bash
   pip install -r requirements.txt
   pip install -e .
   ```

3. Analyse the data yourself using the jupyter notebook and play with the dashboard

   - Open the jupyter notebook

     ```bash
     jupyter lab
     ```

   - Start the dashboard server

     ```bash
     covid19_dashboard
     ```
