## Der Dozent

Max Harlow
Bloomberg News
Max Harlow is a data reporter at Bloomberg News. He also runs Journocoders, a community group for journalists to develop technical skills for use in their reporting.

**Github**: https://github.com/maxharlow/tutorials

## Einige Ansätze

### Browser-Inspektor

### https-request
Was passiert da eigentlich? 
Es gibt zwei Wege, wie eine Website liefert. Entweder direkt oder indirekt, da kommen z.B. die Infos über eine API. 
Wenn das passiert, wird es einfacher zu scrapen. 


### Split fetching and parsing
Fetching = wir lesen das HTML erstmal aus, speichern uns die Seite ab und arbeiten darauf. 
Python oder Javascript sind die besten Sprachen dafür. 

### Prob 1 - Captchas
Es gibt da wohl 3rd-Party-Anbieter? 
Seiten, die auf Publikumsverkehr angewiesen sind wie Shops oder so, machen das vermutlcih seltener. 

#### Solve Captchas locally
Meistens gibt es eine Audio-Version des Captchas, damit es barrierefrei ist. Dann kann man es mit whisper oder anderen Sprachmodellen gut übersetzen. 

#### Captcha farms
Der klassische Weg, das sind die Drittanbieter. Man sendet das Captcha per API an einen Dienst, wo echte Menschen das Captcha lösen. Das ist erstaunlich schnell und günstig. 
bit.ly/eijc26-unscrapable-captchas
https://colab.research.google.com/drive/1E2VxRwSGCQetMgyinA5r2BWQSmUHwGuE

Man sucht den sitekey des captachs (einfach "sitekey" in die Suche eingeben), dann an 
https://2captcha.com/
weiterleiten. 
Andere Dienste: Death by Captcha, Capsolver, Anti Captcha, CapMonster Cloaud, NextCaptcha (kostet nur 50cent pro 1000 Captchas, dauert aber 6 Sekunden, sonst nur 3 Sekunden)

ABER: Das macht den Code langsame, es kostet Geld (etwa 1-3 Euro pro 1000 Captchas)


### Prob 2 - IP-Blocking
Häufig denkt der Server, dass unterschiedliche Anfragen von immer derselben IP stammen. 
Egal warum, er sagt: Nicht über diese IP-Adresse. 

#### Rate limiting
Viele Seiten wollen nicht gescraped werden, weil sie den Traffic nicht bewältigen können. 
Manchmal wollen die Anbieter nicht, dass ihr Service kopiert wird. 


#### Thor
Macht es etwas langsamer

#### Proxies
Normalerweise landet meine Anfrage mit IP-Adresse beim Anbieter. 
Ich kann aber auch über einen Proxy gehen, dann sieht der Anbieter nur die IP des Proxys. 
Die Proxies wechseln normalerweise die IPs durch, damit sie nicht selbst geblockt werden. 

Unter ip.me sehe ich meine eigene IP-Adresse. 

bit.ly/eijc26-unscrapable-proxies
https://colab.research.google.com/drive/1wMibpC8FrK97BzooV4hFeRFyOBbTV85B

Damit kann man mal testen, wie man die IP ändern kann. 
Ein guter Dienst dafür ist **https://decodo.com/#gref**

ab 10 cent pro 1000 Aufrufe. 

Billige Dienste nutzen großen Datacenter. Das Problem dabei: Das merken die aufgerufenen Seiten. 
Besser: Residential sources, teurer, langsamer, aber zuverlässiger. 
Guter Dienst: **bright data, honeygain, oxylabs, infatica.io etc.**
Noch mächtiger: Mobile-Phone-IPs. Kostet aber noch mehr und ist noch langsamer. 

**Woher kommen diese IP-Adressen eigentlich?**
So richtig klar ist das nicht. Einige Anbieter bezahlen Leute dafür. 

**Grenzen der Angebote**
Viele Firmen sind bei .gov-Adressen vorsichtig, andere haben eine Liste mit Seiten, die mit ihnen gescrapt werden dürfen. 
Oxylabs gibt manchmal freie APIs für Journalisten. 

**Was kostet der Spaß?**
Gratis- oder Billigangebote sind meist nichts. 
Häufig:4$ pro Gigabyte. 

### Prob 3 - fingerprinting
Hier wird versucht, den User über sein Verhalten zu kataogisieren. 
Die Browser schauen sich an, wie man mit der Website umgeht. 
Bsp: Wenn ein Button 1000-mal in einer Sekunde geklickt wird, ist das vermutlich kein Mensch. 
Es gibt da wohl so eine Art Chromeextension...
Die Systeme gucken: Passen Sprache, Spracheinstellung und timezone zusammen? 
Bewegt sich die Maus natürlich? etc.
browserscan.net


Lösungen: 
Wir müssen den richtigen Header nutzen
curlconverter.com - 
Zwei Libs curl-cffi (Python) oder impit (Javascript)

Und: Headless browsers - selenium pupeteer, playwright

Außerdem: Stealth-Browsers Camoufox, CloakBrosers etc. 

Und: Web unblokcers & browsers-as-a-service
Die Dienste sind nicht ganz  billig wie brigtdata, oxylabs, rayobyte, aoify, browserless, rebrowser etc. 
Die Preispolitik ist sehr unterschiedlich, aber günstig ist es nicht. 

bit.ly/eijc26-unscrapable



### Scraping Social Media
Linkedin verkauft seine Daten als Produkt. 
Andere sind schwer und sie wehren sich rechtlich (muss da echt mal Berlin fragen)





