import requests
import json
import math
import time
from datetime import datetime,timezone
from utils import config



headers = {
    "Authorization": f"Bearer {config.PROD_API_KEY}",
    "x-api-key": config.PROD_API_KEY,
    "Accept":"application/json",
    "User-agent":"BatchLakeHouseTester/2.0"
}



def get_prod_by_cats(cat:str):
    res = None
    try:
        if not isinstance(cat,str) or not cat.strip():
            raise TypeError(f"Expected category as a non-empty string, got: {type(cat).__name__}")

        
        all_results = []
        current_page = 1
        page_size = 100
        total_expected = None
        
        while True: 
            params={"q": "*",
                "category": cat,
                "page":current_page,
                "page_size":page_size,
                }
            
            res = requests.get(
                f"{config.PROD_API_BASE_URL}search",
                headers=headers,
                timeout=10,
                params=params,
            )
        
        
        
            if res.status_code in (401,403):
                print("Header auth rejected")

            res.raise_for_status()

            data = res.json()
            
            if total_expected is None:
                total_expected = data.get("total",0) or 0
                total_pages = math.ceil(total_expected/page_size) if total_expected else 1
                print(f"Found {total_expected} total items across ~{total_pages} pages.")
                
            page_items = data.get("results",[])
            
            if not page_items:
                break
            
            
            all_results.extend(page_items)
            
            print(f"Page {current_page}: fetched {len(page_items)} items (Progress: {len(all_results)}/{total_expected})")

            if(len(all_results) >= total_expected):
                break
            
            current_page +=1
            
            time.sleep(1)


            #print(formatted_json[:1000])
            
        consolidated_payload = {
            "total":len(all_results)
            ,"category":cat
            ,"ingest_at": datetime.now(timezone.utc).isoformat()
            ,"results": all_results
            
        }
        print(f"Retrieved {len(all_results)} items for '{cat}'")
        formatted_json = json.dumps(consolidated_payload, indent=2, ensure_ascii=False)
        return formatted_json
    
    except TypeError as err_type:
        print(f"Validation Error: {err_type}")
        return None
    except requests.exceptions.HTTPError as err_http:
        print(f"HTTP error {err_http}")
        print(f"Response body: {res.text}")
        return None
        
    except requests.exceptions.RequestException as err:
        print(f"Request Failed: {err}")
        return None


def get_cats():
    
    try:
        res = requests.get(
            f"{config.PROD_API_BASE_URL}categories",
            headers=headers,
            timeout=10,
        )
        
        if res.status_code in (401,403):
            print("Header auth rejected")
        
        res.raise_for_status()
        
        data = res.json()
        
        formatted_json = json.dumps(data, indent=2, ensure_ascii=False)
        
        print(formatted_json[:10000])
        
        return formatted_json
    except requests.exceptions.HTTPError as err_http:
        print(f"HTTP error {err_http}")
    except requests.exceptions.RequestException as err:
        print(f"Request failed: {err}")
        
