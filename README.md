[![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/s-weigand/covid19-data-analyzer/master?urlpath=lab%2Ftree%2Fdev_nb.ipynb)

# covid19-data-analyzer

Especially in times of crisis and panic, with many different opinions on the topic, people should try to derive their own conclusion.
Luckily we live in a time, where the skills and tools to analyse data are open to everyone.
Thus this little project tries to provide you with the data and a small toolset
to understand, what the current state of the covid19 pandemic is right now.

This wil also be the basis for [istcoronaexponentiell.de](https://vm-1.istcoronaexponentiell.de/),
where this projects interactive dashboard will be hosted.

# Usage

1. Clone or download this repository

2. Install the dependencies

   ```
   pip install -r requirements.txt
   ```

3. Analyse the data yourself using the jupyter notebook and play with the dashboard

   - Open the jupyter notebook

     ```
     jupyter lab
     ```

   - Start the dash server

     ```
     python dashboard.py
     ```
