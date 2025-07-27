import requests
from bs4 import BeautifulSoup
import time
import re

# Your Discord webhook URL
DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/1399087297949077564/ljG-OC4xi5nAYIUFq9ulxHkAPiYo4RvwLKj_uOwD6kTIuluSNQGkoKcQ3Jyj5EYhk4Bq"

# Configuration
CHECK_INTERVAL = 300  # 5 minutes
KEYWORDS = ["web development", "frontend", "react", "javascript", "node", "html", "css", "angular", "vue", "website", "web app"]

# URLs to search (web development specific)
SEARCH_URLS = [
    "https://www.freelancer.com/jobs/javascript/",
    "https://www.freelancer.com/jobs/html/",
    "https://www.freelancer.com/jobs/website-design/",
    "https://www.freelancer.com/jobs/php/",
    "https://www.freelancer.com/jobs/css/"
]

# Track seen jobs
seen_jobs = set()

def send_discord_notification(title, link, budget, description):
    """Send job notification to Discord"""
    # Clean and truncate description
    clean_desc = BeautifulSoup(description, 'html.parser').get_text(separator=' ', strip=True)
    truncated_desc = clean_desc[:400] + '...' if len(clean_desc) > 400 else clean_desc
    
    message = (
        f"🔥 **New Web Dev Job Found!**\n"
        f"📋 **Title:** {title}\n"
        f"💰 **Budget:** {budget}\n"
        f"🔗 **Link:** {link}\n"
        f"📝 **Description:**\n{truncated_desc}"
    )
    
    try:
        response = requests.post(
            DISCORD_WEBHOOK_URL,
            json={"content": message},
            headers={'Content-Type': 'application/json'},
            timeout=10
        )
        if response.status_code == 204:
            print(f"✅ Notification sent: {title}")
            return True
        else:
            print(f"❌ Discord error: {response.status_code}")
            return False
    except Exception as e:
        print(f"🚨 Notification failed: {e}")
        return False

def is_relevant(title, description):
    """Check if job matches our keywords"""
    combined = f"{title} {description}".lower()
    
    matched_keywords = []
    for keyword in KEYWORDS:
        if keyword.lower() in combined:
            matched_keywords.append(keyword)
    
    if matched_keywords:
        print(f"✅ Found keywords: {matched_keywords}")
        return True
    
    return False

def extract_budget(card_html):
    """Extract budget from job card HTML"""
    try:
        # Look for common budget patterns
        budget_patterns = [
            r'\$(\d+(?:,\d+)?(?:\.\d+)?)\s*-\s*\$(\d+(?:,\d+)?(?:\.\d+)?)',
            r'\$(\d+(?:,\d+)?(?:\.\d+)?)',
            r'(\d+(?:,\d+)?(?:\.\d+)?)\s*USD',
            r'Budget:\s*([^<\n]+)'
        ]
        
        for pattern in budget_patterns:
            match = re.search(pattern, str(card_html), re.IGNORECASE)
            if match:
                return match.group(0).strip()
        
        return "Not specified"
    except:
        return "Not specified"

def scrape_freelancer_simple():
    """Scrape Freelancer using requests + BeautifulSoup"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1'
    }
    
    total_relevant_jobs = 0
    
    for url in SEARCH_URLS:
        try:
            print(f"\n🌐 Scraping: {url}")
            
            response = requests.get(url, headers=headers, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Look for job cards using multiple selectors
            job_cards = (
                soup.find_all('div', class_='JobSearchCard-item') or
                soup.find_all('div', class_='project-item') or
                soup.find_all('div', class_='project-card')
            )
            
            print(f"📋 Found {len(job_cards)} job cards")
            
            jobs_processed = 0
            for i, card in enumerate(job_cards[:10]):  # Process first 10 jobs per URL
                try:
                    # Find job title and link
                    title_link = card.find('a', href=lambda x: x and '/projects/' in x)
                    
                    if not title_link:
                        continue
                    
                    title = title_link.get_text(strip=True)
                    link = title_link.get('href', '')
                    
                    # Ensure full URL
                    if link and not link.startswith('http'):
                        link = 'https://www.freelancer.com' + link
                    
                    if not title or not link or link in seen_jobs:
                        continue
                    
                    # Extract budget
                    budget = extract_budget(card)
                    
                    # Get full description from card
                    description = card.get_text(separator=' ', strip=True)
                    
                    print(f"\n📝 Job {i+1}: {title}")
                    print(f"🔗 Link: {link}")
                    print(f"💰 Budget: {budget}")
                    
                    # Check if relevant
                    if is_relevant(title, description):
                        if send_discord_notification(title, link, budget, description):
                            total_relevant_jobs += 1
                            print(f"🎯 Relevant job sent to Discord!")
                        else:
                            print(f"❌ Failed to send notification")
                    else:
                        print(f"⏭️ Job not relevant to web development")
                    
                    seen_jobs.add(link)
                    jobs_processed += 1
                    
                except Exception as e:
                    print(f"❌ Error processing job {i+1}: {e}")
                    continue
            
            print(f"✅ Processed {jobs_processed} jobs from {url}")
            time.sleep(3)  # Be respectful to the server
            
        except requests.RequestException as e:
            print(f"🚨 Network error scraping {url}: {e}")
            continue
        except Exception as e:
            print(f"🚨 Error scraping {url}: {e}")
            continue
    
    return total_relevant_jobs

def main():
    """Main monitoring loop"""
    print("🚀 Freelancer Web Dev Job Monitor (No Browser Required)!")
    print(f"🔍 Keywords: {', '.join(KEYWORDS)}")
    print(f"🌐 Searching {len(SEARCH_URLS)} job categories")
    print(f"⏱️ Check interval: {CHECK_INTERVAL} seconds")
    
    # Send startup notification
    if send_discord_notification(
        "🚀 BROWSER-FREE BOT STARTED", 
        "https://www.freelancer.com", 
        "N/A", 
        "Freelancer job monitor is running using requests + BeautifulSoup (no browser dependencies)!"
    ):
        print("✅ Startup notification sent!")
    
    # Main monitoring loop
    while True:
        print(f"\n{'='*60}")
        print(f"[{time.ctime()}] Starting job search cycle...")
        print(f"{'='*60}")
        
        try:
            relevant_jobs = scrape_freelancer_simple()
            
            print(f"\n📊 **SEARCH SUMMARY**:")
            print(f"🎯 Relevant jobs found this cycle: {relevant_jobs}")
            print(f"👀 Total unique jobs seen: {len(seen_jobs)}")
            print(f"⏳ Next search in {CHECK_INTERVAL} seconds...")
            
        except KeyboardInterrupt:
            print("\n🛑 Bot stopped by user")
            break
        except Exception as e:
            print(f"🚨 Unexpected error in main loop: {e}")
        
        # Wait before next cycle
        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    main()
