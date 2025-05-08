import requests
import sys
from html.parser import HTMLParser


class MyHTMLParser(HTMLParser):
    rawhides = list()
    def handle_data(self, data):
        if data.startswith("Fedora-Rawhide-"):
            self.rawhides.append(data)
        

def show_rawhides(limit):
    url = "https://kojipkgs.fedoraproject.org/compose/rawhide/"
    response = requests.get(url)
    if response.status_code == 200:
        parser = MyHTMLParser()
        parser.feed(response.text)
        limited_rawhides = parser.rawhides
        if limit <= len(parser.rawhides):
            limited_rawhides = parser.rawhides[-limit:]
        for x in limited_rawhides:
            print(x)
    else:
        print("Could not read URL: {url}")

def diff_compose(compose1, compose2):
    compose1_url = "https://kojipkgs.fedoraproject.org/compose/rawhide/" + compose1 + "/compose/metadata/rpms.json"
    compose2_url = "https://kojipkgs.fedoraproject.org/compose/rawhide/" + compose2 + "/compose/metadata/rpms.json"
    response = requests.get(compose1_url)
    compose1_data = response.json()
    response = requests.get(compose2_url)
    compose2_data = response.json()
    
    rpms1 = compose1_data['payload']['rpms']['Everything']['x86_64']
    rpms2 = compose2_data['payload']['rpms']['Everything']['x86_64']
    
    # Loop the first set of composes and search each package in the second loop looking for changes
    for package in rpms1.keys():
        package_name = package.rsplit("-", 2)[0]
        package_version = '-'.join(package.rsplit('-', 2)[1:]).rsplit('.', 2)[0]
        
        # I admit I had to use AI to generate this matching expression. It was quite complex
        # to search the package name in the second set of composes, since the json property includes name and version.
        # There might be some misbehaviour with similar package names (i.e. "kernel" and "kernel-dev")
        matches = {key: value for key, value in rpms2.items() if package_name in key}
        
        if matches:
            package2 = next(iter(matches.keys()))
            package2_version = '-'.join(package2.rsplit('-', 2)[1:]).rsplit('.', 2)[0]
            if package_version != package2_version:        
                print(package_name + " CHANGED (" + package_version + " -> " + package2_version + ")")
        else:
            print(package_name + " REMOVED (" + package_version + ")")
    
    # Loop the second compose looking for new added packages
    for package in rpms2.keys():
        package2_name = package.rsplit("-", 2)[0]
        package2_version = '-'.join(package.rsplit('-', 2)[1:]).rsplit('.', 2)[0]
        
        matches = {key: value for key, value in rpms1.items() if package_name in key}
        
        if not matches:
            print(package2_name + " ADDED (" + package2_version + ")")
    

def main():

    # Very basic CLI options filtering
    if len(sys.argv) < 2:
        print("""Usage: python test.py [COMMAND]
        COMMANDS:
        --show-rawhides <limit>
        --diff <compose1> <compose2>
        """)
        sys.exit(1)
    

    command = sys.argv[1]
    if command == "--show-rawhides":
        if len(sys.argv) != 3:
            print("Usage: python test.py --show-rawhides <limit>")
            sys.exit(1)
        if sys.argv[2] is not None:
            limit = int(sys.argv[2])
        show_rawhides(limit)
    else:
        if command == "--diff":
            if len(sys.argv) != 4:
                print("Usage: python test.py --diff <compose1> <compose2>")
                sys.exit(1)
            diff_compose(sys.argv[2], sys.argv[3])

if __name__ == "__main__":
    main()

