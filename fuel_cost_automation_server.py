import base64
import time
import logging
import os
import random
import json

import requests
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (NoSuchElementException,
                                        TimeoutException,
                                        WebDriverException)

from webdriver_manager.chrome import ChromeDriverManager
from mcp.server.fastmcp import FastMCP

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("../web_scraping.log", encoding='utf-8', mode='w'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Initialize FastMCP server
mcp = FastMCP("fuel_cost_update")


def configure_browser(headless=True, proxy=None):
    """
    Configure Chrome browser options

    Args:
        headless (bool): Run browser in background
        proxy (str): Proxy server address (e.g., "ip:port")

    Returns:
        WebDriver: Configured Chrome browser instance
    """
    chrome_options = webdriver.ChromeOptions()

    # Basic configuration
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-infobars")
    chrome_options.add_argument("--disable-notifications")
    chrome_options.add_argument("--start-maximized")
    chrome_options.binary_location = r"C:\Program Files\Google\Chrome\Application\chrome.exe"

    # Headless mode
    if headless:
        chrome_options.add_argument("--headless=new")

    # Proxy settings
    if proxy:
        chrome_options.add_argument(f"--proxy-server={proxy}")

    # Anti-detection settings
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)

    # User agent rotation (optional)
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Safari/605.1.15",
        "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1"
    ]
    chrome_options.add_argument(f"user-agent={random.choice(user_agents)}")

    # Initialize browser
    try:
        # Automatic driver management
        service = Service(executable_path=ChromeDriverManager().install())

        # Initialize browser
        browser = webdriver.Chrome(service=service, options=chrome_options)

        # Additional stealth settings
        browser.execute_script(
            "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
        )

        return browser

    except WebDriverException as e:
        logger.error(f"Browser initialization failed: {str(e)}")
        raise


@mcp.tool(description="Scrape target website HKE with error handling and retries in url")
def scrape_website_HKE(url: str="https://www.hkelectric.com/zh/our-operations/scheme-of-control/tariff-components-and-tariff-information/monthly-fuel-clause-charge",
                        max_retries: int=3,
                        wait_time: int=10):
    """
    Scrape target website HKE with error handling and retries

    Args:
        url (str): Target URL https://www.hkelectric.com/zh/our-operations/scheme-of-control/tariff-components-and-tariff-information/monthly-fuel-clause-charge to scrape
        max_retries (int): Maximum retry attempts
        wait_time (int): Seconds to wait between retries
    """
    data1 = []
    data2 = []
    data3 = []
    retries = 0

    while retries < max_retries:
        try:
            # Configure browser (headless by default)
            browser = configure_browser(headless=True)

            logger.info(f"Attempting to scrape: {url} (Attempt {retries + 1}/{max_retries})")

            # Navigate to target URL
            browser.get(url)

            # Wait for page to load
            WebDriverWait(browser, 20).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            logger.info("Page loaded successfully")

            # Scroll to bottom (for lazy-loaded content)
            browser.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)  # Allow time for loading

            # ===== CUSTOM SCRAPING LOGIC =====
            # Replace this section with your specific scraping requirements

            # Extract Table 1

            t1_content = {}
            # Get the table header
            div_header_container = WebDriverWait(browser, 20).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div.jss143.jss166.MuiBox-root.css-xx4go0"))
            )
            head1 = div_header_container.find_element(By.TAG_NAME, "p")
            head2 = div_header_container.find_element(By.CSS_SELECTOR, "div.sessionBody.jss146.MuiBox-root.css-0")

            t1_content["header"] = f"{head1.text} \n {head2.text}"

            # Get the table content
            div_container = WebDriverWait(browser, 20).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.tableContainer.jss95.MuiBox-root.css-0"))
            )


            # 定位DIV内部的<table>标签
            table = div_container[0].find_element(By.TAG_NAME, "table")

            # 提取所有行
            rows = table.find_elements(By.TAG_NAME, "tr")

            # 提取每行的单元格（td或th）
            column_cells_t1 = rows[0].find_elements(By.TAG_NAME, "th")
            data_cells1_t1 = rows[1].find_elements(By.TAG_NAME, "td")

            column_name_t1 = [cell.text for cell in column_cells_t1]
            row_data1_t1 = [cell.text for cell in data_cells1_t1]
            print(f"{column_name_t1} \n")
            print(f"{row_data1_t1}")
            print("===========")

            data1.append({
                column_name_t1[0]: [row_data1_t1[0]],
                column_name_t1[1]: [row_data1_t1[1]],
                column_name_t1[2]: [row_data1_t1[2]]
            })
            t1_content["data"] = data1



            # Extract table 2
            t2_content = {}

            # Get header
            t2_content["header"] = t1_content["header"]


            # Get table content
            # 定位DIV内部的<table>标签
            table = div_container[1].find_element(By.TAG_NAME, "table")

            # 提取所有行
            rows = table.find_elements(By.TAG_NAME, "tr")

            column_cells_t2 = rows[0].find_elements(By.TAG_NAME, "th")
            data_cells1_t2 = rows[1].find_elements(By.TAG_NAME, "td")
            data_cells2_t2 = rows[2].find_elements(By.TAG_NAME, "td")
            data_cells3_t2 = rows[3].find_elements(By.TAG_NAME, "td")
            data_cells4_t2 = rows[4].find_elements(By.TAG_NAME, "td")
            data_cells5_t2 = rows[5].find_elements(By.TAG_NAME, "td")
            data_cells6_t2 = rows[6].find_elements(By.TAG_NAME, "td")

            column_name_t2 = [cell.text for cell in column_cells_t2]
            row_data1_t2 = [cell.text for cell in data_cells1_t2]
            row_data2_t2 = [cell.text for cell in data_cells2_t2]
            row_data3_t2 = [cell.text for cell in data_cells3_t2]
            row_data4_t2 = [cell.text for cell in data_cells4_t2]
            row_data5_t2 = [cell.text for cell in data_cells5_t2]
            row_data6_t2 = [cell.text for cell in data_cells6_t2]
            print(f"{column_name_t2} \n")
            print(f"{row_data1_t2} \n {row_data2_t2} \n {row_data3_t2} \n {row_data4_t2} \n {row_data5_t2} \n {row_data6_t2}")

            data2.append({
                column_name_t2[0]: [row_data1_t1[0], row_data2_t2[0], row_data3_t2[0], row_data4_t2[0], row_data5_t2[0], row_data6_t2[0]],
                column_name_t2[1]: [row_data1_t1[1], row_data2_t2[1], row_data3_t2[1], row_data4_t2[1], row_data5_t2[1], row_data6_t2[1]],
                column_name_t2[2]: [row_data1_t1[2], row_data2_t2[2], row_data3_t2[2], row_data4_t2[2], row_data5_t2[2], row_data6_t2[2]]
            })
            t2_content["data"] = data2

            # Extract table 3
            t3_content = {}
            # Get header

            t3_content["header"] = t1_content["header"]

            # 定位DIV内部的<table>标签
            table = div_container[2].find_element(By.TAG_NAME, "table")

            # 提取所有行
            rows = table.find_elements(By.TAG_NAME, "tr")

            column_cells_t3 = rows[0].find_elements(By.TAG_NAME, "th")
            data_cells1_t3 = rows[1].find_elements(By.TAG_NAME, "td")

            column_name_t3 = [cell.text for cell in column_cells_t3]
            row_data1_t3 = [cell.text for cell in data_cells1_t3]
            print(f"{column_name_t3} \n")
            print(f"{row_data1_t3}")
            print("===========")

            data3.append({
                column_name_t3[0]: [row_data1_t3[0]],
                column_name_t3[1]: [row_data1_t3[1]],
                column_name_t3[2]: [row_data1_t3[2]],
                column_name_t3[3]: [row_data1_t3[3]],
                column_name_t3[4]: [row_data1_t3[4]],
                column_name_t3[5]: [row_data1_t3[5]],
                column_name_t3[6]: [row_data1_t3[6]],
                column_name_t3[7]: [row_data1_t3[7]]
            })
            t3_content["data"] = data3

            # Extract image
            container = WebDriverWait(browser, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div.imageItemContainer.MuiBox-root.css-0"))
            )

            # Locate the <img> tag inside the container
            img_tag = container.find_element(By.TAG_NAME, "img")

            # Extract image attributes
            image_title = img_tag.get_attribute("title") or img_tag.get_attribute("alt") or "untitled"
            image_src = img_tag.get_attribute("src")

            print(f"Image Title: {image_title}")
            print(f"Image Source: {image_src}")

            img = {}
            # Download the image
            if image_src:
                # Create a directory to save images
                os.makedirs("../downloaded_images", exist_ok=True)

                if image_src.startswith("data:image"):
                    # Handle base64 encoded images
                    header, encoded = image_src.split(",", 1)
                    image_data = base64.b64decode(encoded)
                    file_ext = header.split("/")[1].split(";")[0]  # e.g., "png"
                else:
                    # Handle normal URL images
                    response = requests.get(image_src, stream=True)
                    image_data = response.content
                    # file_ext = image_src.split(".")[-1].lower()  # Extract extension
                    img = {
                        "image_data": image_data,
                        "title": image_title
                    }

                # # Save the image
                # filename = f"downloaded_images/{image_title[:50]}.{file_ext}"  # Limit title length
                # with open(filename, "wb") as f:
                #     f.write(image_data)
                # print(f"Image saved as: {filename}")

            # ===== END CUSTOM LOGIC =====
            result = {
                        "t1_content_hke": t1_content,
                        "t2_content_hke": t2_content,
                        "t3_content_hke": t3_content,
                        "img": img
                        }
            
            output = json.dumps(result, indent=2, default=str)


            return output

        except (TimeoutException, NoSuchElementException) as e:
            logger.warning(f"Scraping attempt failed: {str(e)}")
            retries += 1
            time.sleep(wait_time * retries)  # Exponential backoff

        finally:
            # Ensure browser closes even on errors
            if 'browser' in locals():
                browser.quit()
                logger.info("Browser closed")


@mcp.tool(description="Scrape target website CLP with error handling and retries in url")
def scrape_website_CLP(url: str="https://www.clp.com.hk/zh/help-support/bills-payment-tariffs/fuel-cost-adjustment",
                        max_retries: int=3,
                        wait_time: int=10):
    """
    Scrape target website CLP with error handling and retries

    Args:
        url (str): Target URL https://www.clp.com.hk/zh/help-support/bills-payment-tariffs/fuel-cost-adjustment to scrape
        max_retries (int): Maximum retry attempts
        wait_time (int): Seconds to wait between retries
    """
    retries = 0

    while retries < max_retries:
        try:
            # Configure browser (headless by default)
            browser = configure_browser(headless=True)

            logger.info(f"Attempting to scrape: {url} (Attempt {retries + 1}/{max_retries})")

            # Navigate to target URL
            browser.get(url)

            # Wait for page to load
            WebDriverWait(browser, 20).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            logger.info("Page loaded successfully")

            # Scroll to bottom (for lazy-loaded content)
            browser.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)  # Allow time for loading


            ### Extract image
            # Locate the img header
            header_container = WebDriverWait(browser, 10).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.clphk-pagebody"))
            )

            img_header_tag = header_container[0].find_element(By.TAG_NAME, "h2")
            logger.info(f"Image Title: {img_header_tag.text}")

            # Locate the <img> tag inside the container
            img_container = WebDriverWait(browser, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div.cmp-image"))
            )

            img_tag = img_container.find_element(By.TAG_NAME, "img")

            # Extract image attributes
            # image_title = img_tag.get_attribute("title") or img_tag.get_attribute("alt") or "untitled"
            image_src = img_tag.get_attribute("src")


            logger.info(f"Image Source: {image_src}")

            img = {}
            # Download the image
            if image_src:
                # Create a directory to save images
                os.makedirs("../downloaded_images", exist_ok=True)

                if image_src.startswith("data:image"):
                    # Handle base64 encoded images
                    header, encoded = image_src.split(",", 1)
                    image_data = base64.b64decode(encoded)
                    file_ext = header.split("/")[1].split(";")[0]  # e.g., "png"
                else:
                    # Handle normal URL images
                    response = requests.get(image_src, stream=True)
                    image_data = response.content
                    # file_ext = image_src.split(".")[-1].lower()  # Extract extension
                    img = {
                        "image_data": image_data,
                        "title": img_header_tag.text
                    }


            # Extract table 1
            t1_content_clp = {}
            data1_clp = []
            # Get header
            t1_content_clp["header"] = img_header_tag.text

            # 定位DIV内部的table
            div_header_container = WebDriverWait(browser, 20).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.clphk-tableheader__row.clphk-tableheader__row--header"))
            )

            table1_head_col = div_header_container[0].find_elements(By.CSS_SELECTOR, "div.clphk-tableheader__cell.clphk-tableheader__cell--header")

            table1_head_col_data = [cell.text for cell in table1_head_col if cell.text != '']


            div_row_container = WebDriverWait(browser, 20).until(
                EC.presence_of_all_elements_located(
                    (By.CSS_SELECTOR, "div.clphk-tablebody__row.clphk-tablebody__row--content"))
            )
            logger.info(len(div_row_container))

            table1_row_col = div_row_container[0].find_elements(By.CSS_SELECTOR,
                                                                "div.clphk-tablebody__cell.clphk-tablebody__cell--content")
            logger.info(len(table1_row_col))
            table1_body_row_data = []
            for  row_cell in table1_row_col:
                p_elements = row_cell.find_elements(By.TAG_NAME, "p")
                for p_element in p_elements:
                    table1_body_row_data.append(p_element.text)

            table1_body_row_data[0] = table1_body_row_data[0] + table1_body_row_data[1]
            del table1_body_row_data[1]
            logger.info(f"Table 1: {table1_head_col_data}")
            logger.info(f"Table 1: {table1_body_row_data}")

            temp = {}
            if len(table1_head_col_data) == len(table1_body_row_data):
                for i in range(len(table1_head_col_data)):
                    temp[table1_head_col_data[i]] = [table1_body_row_data[i]]
            data1_clp.append(temp)
            t1_content_clp["data"] = data1_clp
            logger.info(f"Successfully scraped: \n {t1_content_clp}")


            # Extract table 2
            t2_content_clp = {}
            data2_clp = []

            header_str = ''
            # Get the header
            t2_header_tag1 = header_container[1].find_element(By.TAG_NAME, "h2")
            header_str = header_str + t2_header_tag1.text + '\n'

            div_t2h_container = WebDriverWait(browser, 20).until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, "div.highlight-text"))
            )
            t2h_content = div_t2h_container.find_element(By.CSS_SELECTOR, "div.clphk-highlight-text-content")
            header_str = header_str + t2h_content.text + '\n'

            t2_header_tag2 = header_container[2].find_elements(By.TAG_NAME, "p")
            for p_element in t2_header_tag2:
                header_str = header_str + p_element.text + '\n'

            t2_content_clp["header"] = header_str

            logger.info(f"t2 Header : {header_str}")
            # Get the table2 content
            table2_head_col = div_header_container[1].find_elements(By.CSS_SELECTOR,
                                                                    "div.clphk-tableheader__cell.clphk-tableheader__cell--header")

            table2_head_col_data = [cell.text for cell in table2_head_col if cell.text != '']

            # t2 row 1
            table2_row1_col = div_row_container[1].find_elements(By.CSS_SELECTOR,
                                                                "div.clphk-tablebody__cell.clphk-tablebody__cell--content")

            table2_body_row1_data = []
            for row_cell in table2_row1_col:
                p_elements = row_cell.find_elements(By.TAG_NAME, "p")
                for p_element in p_elements:
                    table2_body_row1_data.append(p_element.text)

            # t2 row 2
            table2_row2_col = div_row_container[2].find_elements(By.CSS_SELECTOR,
                                                                "div.clphk-tablebody__cell.clphk-tablebody__cell--content")

            table2_body_row2_data = []
            for row_cell in table2_row2_col:
                p_elements = row_cell.find_elements(By.TAG_NAME, "p")
                for p_element in p_elements:
                    table2_body_row2_data.append(p_element.text)

            # t2 row 3
            table2_row3_col = div_row_container[3].find_elements(By.CSS_SELECTOR,
                                                                "div.clphk-tablebody__cell.clphk-tablebody__cell--content")

            table2_body_row3_data = []
            for row_cell in table2_row3_col:
                p_elements = row_cell.find_elements(By.TAG_NAME, "p")
                for p_element in p_elements:
                    table2_body_row3_data.append(p_element.text)

            # t2 row 4
            table2_row4_col = div_row_container[4].find_elements(By.CSS_SELECTOR,
                                                                "div.clphk-tablebody__cell.clphk-tablebody__cell--content")

            table2_body_row4_data = ['']
            for row_cell in table2_row4_col:
                p_elements = row_cell.find_elements(By.TAG_NAME, "p")
                for p_element in p_elements:
                    table2_body_row4_data.append(p_element.text)

            temp2 = {}
            if len(table2_head_col_data) == len(table2_body_row1_data):
                for i in range(len(table2_head_col_data)):
                    temp2[table2_head_col_data[i]] = [table2_body_row1_data[i], table2_body_row2_data[i], table2_body_row3_data[i], table2_body_row4_data[i]]
            data2_clp.append(temp2)
            t2_content_clp["data"] = data2_clp
            logger.info(f"Successfully scraped: \n {t2_content_clp}")


            result = {
                        "t1_content_hke": t1_content_clp,
                        "t2_content_hke": t2_content_clp,
                        "img": img
                        }
            
            output = json.dumps(result, indent=2, default=str)


            return output


        except (TimeoutException, NoSuchElementException) as e:
            logger.warning(f"Scraping attempt failed: {str(e)}")
            retries += 1
            time.sleep(wait_time * retries)  # Exponential backoff

        finally:
            # Ensure browser closes even on errors
            if 'browser' in locals():
                browser.quit()
                logger.info("Browser closed")


if __name__ == "__main__":
    # content_json_clp= scrape_website_CLP()
    # content_json_hke = scrape_website_HKE()
    # logger.info(f"==========================Scrape data from CLP: \n {content_json_hke}")
    # content_html_clp = generate_key_value_html(content_json_clp, "CLP")
    # content_html_hke = generate_key_value_html(content_json_hke, "HKE")
    
    # # logger.info(f"++++++++++++++++++++++++++Scrape data from CLP: \n {content_html}")
    # send_status = send_outlook_email_with_content(content_html_clp, content_html_hke, "Monthly Fuel Cost Update", "Austin.ZL.Li@pccw.com")
    # logger.info(f"=============================emaile send status: \n {send_status}")
    print("mcp running")
    mcp.run()