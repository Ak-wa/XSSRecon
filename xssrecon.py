import requests
from parsel import Selector
from colorama import Fore, Back, Style
from time import sleep
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.firefox.options import Options
import threading
import sys
import argparse

class xssRecon:
    def __init__(self,arguments):
        self.target = ""
        self.silent = False
        self.target_links = []
        self.payloads = []
        self.vulns = []
        self.usable_links = []
        self.counter = 0
        self.wordlist = "xss_payloads.txt"
        self.delay = 0
    
    def logo(self):
        print(Fore.GREEN+"""
        

 _     _ _______ _______  ______ _______ _______  _____  __   _
  \___/  |______ |______ |_____/ |______ |       |     | | \  |
 _/   \_ ______| ______| |    \_ |______ |_____  |_____| |  \_|
                                                               

    XSSRecon - Automated refl. XSS Scanner
    http://1337.rocks
    
    Usage: python3 xssrecon.py -h
           python3 xssrecon.py --target http://example.com/index.php?id=1
           python3 xssrecon.py --target http://example.com --crawl
           
"""+Style.RESET_ALL)
    
    def spawn_browser(self, visibility):
        self.options = Options()
        if visibility == False:
            self.options.headless = True
        if visibility == True:
            self.options.headless = False
        self.profile = webdriver.FirefoxProfile() 
        self.profile.set_preference("permissions.default.image", 2)
        self.profile.set_preference("permissions.default.stylesheet", 2);
        self.driver = webdriver.Firefox(options=self.options,firefox_profile=self.profile)

    def crawl_and_test(self, target):
        print(Fore.GREEN+"[i] Starting crawler...")
        self.response = requests.get(self.target)
        self.selector = Selector(self.response.text)
        self.href_links = self.selector.xpath('//a/@href').getall()
        self.image_links = self.selector.xpath('//img/@src').getall()
        if self.silent == False:
            print(Fore.GREEN+"[ ] Looking for usable links (with parameters) in webpage html...")
        if self.href_links == []:
            print(Fore.YELLOW+"[!] No hrefs found")
            self.driver.quit()
            sys.exit()
        else:
            if self.silent == False:
                for href in self.href_links:
                    if "=" in href:
                        print("| %s" % href)
                        self.usable_links.append(href)
                if self.usable_links == []:
                    print("[-] Could not find any usable links in webpage")
        print(Fore.GREEN+"[i] Starting Scanner")
        for payload in self.payloads:
            for link in self.href_links:
                if "=" in link:
                    if not "http" in link:
                        full_link = f"{self.target}/{link}"
                    else:
                        full_link = link
                    equal_counter = full_link.count("=")
                    last_param = full_link.split("=")[equal_counter]
                    for payload in self.payloads:
                        exploit_url = full_link.replace(last_param,payload)
                        self.single_xss_check(str(exploit_url))
        if self.vulns == []:
            print(Fore.GREEN+"[-] No vulnerabilities found")
            self.driver.quit()
            sys.exit()
        else:
            print(Fore.RED+"[+] Found the following exploits:")
            for link in self.vulns:
                print("|", link)
            self.driver.quit()
            sys.exit()
    
    def scan_one_url(self, url):
        print(Fore.GREEN+"[i] Starting single URL scanner...")
        for payload in self.payloads:
            self.single_xss_check(str(url)+str(payload))
        if self.vulns == []:
            print(Fore.GREEN+"[-] No vulnerabilities found")
            self.driver.quit()
            sys.exit()
        else:
            print(Fore.RED+"[+] Found the following exploits:")
            for link in self.vulns:
                print("|", link)
            self.driver.quit()
            sys.exit()

    def single_xss_check(self, url):
        self.counter += 1
        if self.silent == False:
            sys.stdout.write(Fore.GREEN+"[%d] Testing: %s" % (self.counter, url))
        self.driver.get(str(url))
        sleep(int(self.delay))
        try:
            self.driver.switch_to.alert.accept()
            sys.stdout.write(Fore.RED+"\n[+] Found reflected XSS at")
            sys.stdout.write("\n| %s " % url)
            sys.stdout.write(Style.RESET_ALL+"\n")
            vulns.append(exploit_url)
        except:
            sys.stdout.write("\r")
            sys.stdout.flush()


    def parse_payload_file(self):
        if args.wordlist:
            self.wordlist = args.wordlist
        file = self.wordlist
        with open(str(file)) as payloads:
            for payload in payloads:
                payload = payload.rstrip()
                self.payloads.append(payload)

    def argument_parser(self):
        self.logo()
        if args.delay:
            self.delay = args.delay
        if args.silent:
            self.silent = True
        if args.wordlist:
            self.wordlist = args.wordlist
        if args.visible:
            self.spawn_browser(visibility=True)
        else:
            self.spawn_browser(visibility=False)
        if args.target:
            self.target = str(args.target)
            if args.crawl:
                self.crawl_and_test(target=self.target)
            else:
                if "=" in self.target:
                    self.scan_one_url(self.target)
                else:
                    print("[!] Please use --crawl or pass a full url with a parameter to test (e.g http://example.com/index.php?id=1)")
                    self.driver.quit()
                    sys.exit()
  
    def run(self):
        try:
            self.parse_payload_file()
            self.argument_parser()
        except KeyboardInterrupt:
            print(Fore.GREEN+"\n[-] CTRL-C caught, exiting...")
            self.driver.quit()
            sys.exit()
        except Exception as e:
            print(e)
            self.driver.quit()
            sys.exit()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--target", help="Scan a single URL for XSS")
    parser.add_argument("--wordlist", help= "XSS wordlist to use")
    parser.add_argument("--delay", help= "Delay to wait for webpage to load (each test)")
    parser.add_argument("--crawl", help="Crawl page automatically & test everything for XSS", action="store_true")
    parser.add_argument("--silent", help="Silent mode (less output)", action="store_true")
    parser.add_argument("--visible", help="Shows browser while testing (may slow down)", action="store_true")
    args = parser.parse_args()
    #print(args.echo)
    
    scanner = xssRecon(args)
    scanner.run()
