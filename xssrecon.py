#!/usr/bin/env python3
import requests
from parsel import Selector
from colorama import Fore, Back, Style
from time import sleep
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
import threading
import sys
import argparse
import tldextract
from string import digits
from os import system

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
        self.used_parameters = []


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
        self.driver = webdriver.Chrome(options=self.options)

    def crawl_and_test(self, target):
        print(Fore.YELLOW+"[i] Starting crawler...")
        self.response = requests.get(self.target)
        self.selector = Selector(self.response.text)
        self.href_links = self.selector.xpath('//a/@href').getall()
        if self.silent == False:
            print(Fore.YELLOW+"[i] Looking for usable links (with parameters) in webpage html...")
        if self.href_links == []:
            print(Fore.YELLOW+"[i] No hrefs found")
            self.driver.quit()
            sys.exit()
        else:
            if self.silent == False:

                # Follow hrefs
                for href in self.href_links:
                    #print("Current href: {}".format(href))
                    if 'http' in href:
                        response_follow = requests.get(href)
                    else:
                        if href.startswith("/"):
                            response_follow = requests.get(self.target+href)
                        else:
                            response_follow = requests.get(self.target+"/"+href)
                    selector_follow = Selector(response_follow.text)
                    href_links_follow = selector_follow.xpath('//a/@href').getall()

                    # Check mainpage hrefs for parameters
                    if "=" in href:
                        if href not in self.usable_links:
                                if href.startswith("http") or href.startswith("https"):
                                    if self.check_scope(self.target, href):
                                        print(Fore.GREEN+"| %s" % href)
                                        self.usable_links.append(href)
                                    else:
                                        print(f"{Fore.RED}| {href}{Style.RESET_ALL}")
                                else:
                                    if href.startswith("/"):
                                        print(Fore.GREEN+"| %s" % href)
                                        self.usable_links.append(href)
                                    else:
                                        href = "/"+str(href)
                                        print(Fore.GREEN+"| %s" % href)
                    # Check followed page hrefs for parameters
                    for href in href_links_follow:
                        if "=" in href:
                            if href not in self.usable_links:
                                if href.startswith("http") or href.startswith("https"):
                                    if self.check_scope(self.target, href):
                                        print(Fore.GREEN+"| %s" % href)
                                        self.usable_links.append(href)
                                    else:
                                        print(f"{Fore.RED}| {href}{Style.RESET_ALL}")
                                else:
                                    if href.startswith("/"):
                                        print(Fore.GREEN+"| %s" % href)
                                        self.usable_links.append(href)
                                    else:
                                        href = "/"+str(href)
                                        print(Fore.GREEN+"| %s" % href)
                                        self.usable_links.append(href)
                if self.usable_links == []:
                    print("[-] Could not find any usable links in webpage")
        # Scanner
        print(Fore.YELLOW+"[i] Starting Scanner")
        for link in self.usable_links:
            if "=" in link:
                if not "http" in link:
                    full_link = f"{self.target}/{link}"
                else:
                    full_link = link
                equal_counter = full_link.count("=")
                last_param = full_link.split("=")[equal_counter]
                for payload in self.payloads:
                    exploit_url = full_link.replace(last_param,payload)
                    self.single_xss_check(url=str(exploit_url), payload=payload, parameter=(full_link.split("=")[int(equal_counter)-1]))


        if self.vulns == []:
            print(Fore.YELLOW+"[-] No vulnerabilities found")
            self.driver.quit()
            sys.exit()
        else:
            print(Fore.RED+"[+] Found the following exploits:")
            for link in self.vulns:
                print("|", link)
            self.driver.quit()
            sys.exit()

    def parameter_compare(self, param1, param2):
        param1 = param1.translate(None, digits)
        param2 = param2.translate(None, digits)

        if param1 == param2:
            return False
        else:
            return True
    def check_scope(self, target, url):
        self.target_domain = tldextract.extract(self.target).registered_domain

        url_domain = tldextract.extract(url)
        if url_domain.count(".") == 2: # Subdomain check
            print("Subdomain found")
        url_domain = url_domain.registered_domain

        if str(self.target_domain) == str(url_domain):
            #print("[DEBUG] {} and {} are the same domain!".format(self.target_domain, url_domain))
            return True
        else:
            #print("Found out of scope domain: {}:{} with URL: {}".format(self.target_domain, url_domain, url))
            return False

    def scan_one_url(self, url):
        print(Fore.YELLOW+"[i] Starting single URL scanner...")
        equal_counter = url.count("=")
        for payload in self.payloads:
            self.single_xss_check(str(url)+str(payload), payload=payload, parameter = url.split("=")[int(equal_counter)-1])
        if self.vulns == []:
            print(Fore.YELLOW+"[-] No vulnerabilities found")
            self.driver.quit()
            sys.exit()
        else:
            print(Fore.RED+"[+] Found the following exploits:")
            for link in self.vulns:
                print("|", link)
            self.driver.quit()
            sys.exit()

    def single_xss_check(self, url, payload, parameter):
        self.counter += 1
        if self.silent == False:
            #sys.stdout.write(Fore.CYAN+"[%d] Testing: %s" % (self.counter, url))
            sys.stdout.write(Fore.MAGENTA+"""
Parameter: {}
Payload: {}
Counter: {}
""".format(parameter+"=", payload, self.counter))
        self.driver.get(str(url))
        sleep(int(self.delay))
        try:
            self.driver.switch_to.alert.accept()
            sys.stdout.write("\n")
            sys.stdout.write(Fore.RED+"\n[+] Found reflected XSS at")
            sys.stdout.write("\n| %s " % url)
            for i in range(5):
                sys.stdout.write("\n")
            sys.stdout.write(Style.RESET_ALL+"\n")
            vulns.append(exploit_url)
        except:
            sys.stdout.write("\033[F")
            sys.stdout.write("\033[K")
            sys.stdout.write("\033[F")
            sys.stdout.write("\033[K")
            sys.stdout.write("\033[F")
            sys.stdout.write("\033[K")
            sys.stdout.write("\033[F")
            sys.stdout.write("\033[K")
            #sys.stdout.flush()


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
        if args.setup:
            print("[+] Creating /usr/bin/XSSRecon folder")
            system('mkdir /usr/bin/XSSRecon')
            system("mkdir /usr/bin/XSSRecon/bin")
            print("[+] Cloning xssrecon.py into /usr/bin/XSSRecon/bin/XSSRecon")
            system(
                'wget https://raw.githubusercontent.com/Ak-wa/XSSRecon/master/xssrecon.py -O /usr/bin/XSSRecon/bin/xssrecon')
            system("chmod +x /usr/bin/XSSRecon/bin/xssrecon")
            print("[+] Setting up XSSRecon")
            system("ln -s /usr/bin/XSSRecon/bin/xssrecon /usr/local/bin")
            print("[+] Done, you can now use XSSRecon from anywhere! Just type 'xssrecon'")
            sys.exit()
        else:
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
    parser.add_argument("--setup", help="Sets up XSSRecon with symlink to access it from anywhere", action="store_true")
    args = parser.parse_args()
    #print(args.echo)

    scanner = xssRecon(args)
    scanner.run()
