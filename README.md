# Finance
### Finance is an application that uses the IEX api to manage a stock portfolio using SQL, Flask, HTML and CSS.

![](/static/finance2.gif)

## Description
Finance is a Stockmarket simulation using the IEX Api to get real-time stock data.
It can look up stocks, buy or sell them and locks the user history and displays it.
User portfolios, as well as existing accounts, are saved in a Database.

## Getting Started
### 1. Downloading the code 
  ```bash
  $  gh repo clone paulhatdichdolllieb/Finance
  ```
### 2. Setting up the Api Key
   - Create a “Individual” account at [IEX Api](https://iexcloud.io/cloud-login#/register/)
   - At the bottom of the site select “Get started for free” and click “Select Start plan” to choose the free plan. 
   - You can finde yourToken at [Site](https://iexcloud.io/cloud-login?r=https%3A%2F%2Fiexcloud.io%2Fconsole%2Ftokens#/)
   - Copy thekey (beginning with pk_) and execute in your terminal:
       ```bash
       $ export API_KEY=value
       ```
### 3. Running
  - Start flask within Finance/
      ```bash
      $ flask run
      ```


  
