import json
import random
import re
from datetime import timedelta, datetime

import bs4
import requests
from facebook_scraper import get_posts

from add_posts.celery.celery import app
from bs4 import BeautifulSoup
from core import models
from core.helpers import get_proxy, find_value
from django.utils import timezone

from core.models import Post


def get_text_lib(url):
    try:
        post = next(get_posts(post_urls=[url]))
        return post['text']

    except Exception as e:
        print(e)
        return None


def get_text_my(url):
    try:
        response = requests.request("GET", url, headers={
            'authority': 'm.facebook.com',
            'cache-control': 'max-age=0',
            'sec-ch-ua': '"Chromium";v="92", " Not A;Brand";v="99", "Google Chrome";v="92"',
            'sec-ch-ua-mobile': '?1',
            'dnt': '1',
            'upgrade-insecure-requests': '1',
            'user-agent': 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.131 Mobile Safari/537.36',
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
            'sec-fetch-site': 'none',
            'sec-fetch-mode': 'navigate',
            'sec-fetch-user': '?1',
            'sec-fetch-dest': 'document',
            'accept-language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7'

        }, data={})

        bs = bs4.BeautifulSoup(response.text)
        str_bs = str(bs.find("div", {"class": "hidden_elem"}))
        text_with_html = str_bs[str_bs.find("<p>"):str_bs.rfind("</p>")]
        text = re.sub(r'\<[^>]*\>', '', text_with_html)
        return text
    except Exception as e:
        print(e)
        return None


@app.task
def start_update_content():
    for post in Post.objects.filter(content__text__isnull=True).order_by('-id'):
        text = get_text_lib(post.fb_post_link)
        if not text:
            text = get_text_my(post.fb_post_link)
        if text:
            print(text)
            post.content.text = text
            post.content.save()


@app.task
def start_parsing_url():
    headers = {
        'user-agent': 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.131 Mobile Safari/537.36',

        # 'User-Agent': 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/31.0.1650.59 Safari/537.36',
    }
    proxy = get_proxy()
    if proxy is None:
        return
    print(proxy)
    proxies = {'https': 'https://{}:{}@{}:{}'.format(proxy.login, proxy.password, proxy.host, str(proxy.port))}
    post_url = \
        models.PostUrl.objects.filter(is_ready=False, is_successful=True,
                                      is_parsing=False).order_by('added_date').first()
    if post_url is not None:
        post_url.is_parsing = True
        post_url.save()
        res = None
        try:
            print(post_url.db_post_url)
            res = requests.get(post_url.db_post_url, proxies=proxies, headers=headers, timeout=60).text
            owner_fb_id = find_value(res, '",id:', num_sep_chars=1, separator='"')
            if owner_fb_id is None:
                owner_fb_id = find_value(res, ';id=', num_sep_chars=0, separator='&')
            user_name = find_value(res, ';fref=nf">', num_sep_chars=0, separator='<', is_first=True)
            if user_name is None:
                user_name = find_value(res, '=C-R">', num_sep_chars=0, separator='<', is_first=True)
                if user_name is None:
                    user_name = find_value(res, '<strong class="actor">', num_sep_chars=0, separator='<',
                                           is_first=True)
            text = None
            try:
                beatiful_text = find_value(res, '><div><p>', num_sep_chars=0, separator='</p></div>', is_first=True)
                print(beatiful_text)
                text = BeautifulSoup(
                    find_value(res, '><div><p>', num_sep_chars=0, separator='</p></div>', is_first=True)).text
            except Exception as e:
                print(e)
                pass
            if text is None:
                html = BeautifulSoup(res, 'html')
                text = html.text
            comment = find_value(res, '_comment_count', num_sep_chars=2, separator='"', is_first=True)
            reaction = find_value(res, 'reaction_count:{count:', num_sep_chars=0, separator='}')
            if reaction is None:
                reaction = find_value(res, "like_count:", num_sep_chars=0, separator=',', is_first=True)

            share = find_value(res, '_share_count', num_sep_chars=2, separator='"', is_first=True)
            user = models.User.objects.filter(fb_id=owner_fb_id).first()
            if user is None:
                user_url = find_value(res, '><strong><a href="', num_sep_chars=0, separator='"', is_first=True)
                if user_url is None:
                    user_url = find_value(res, '"actor-link" href="', num_sep_chars=0, separator='"', is_first=True)
                user_url = user_url[:user_url.find(',')]
                user_url = user_url[:user_url.find('"')]
                user_url = user_url[:user_url.find('&')]
                user_url = user_url[:user_url.find('_')]
                user_url = user_url[:user_url.find('?refid=1')]
                if user_url[-1] == "?":
                    user_url = user_url[:-1]
                full_url = "https://www.facebook.com" + user_url
                user = models.User.objects.filter(link=full_url).first()
                if user is None:
                    user = models.User.objects.create(name=user_name, link=full_url, fb_id=owner_fb_id)
            print("user" + str(user.id))
            state = models.PostStat.objects.create(likes=reaction, comments=comment, shares=share)
            print("state" + str(state.id))

            content = models.Content.objects.create(text=text)
            print("content" + str(content.id))
            print("post_url.task_id" + str(post_url.task_id))
            task = models.Task.objects.get(id=int(post_url.task_id))
            print("task" + str(task.id))
            #
            post = models.Post.objects.create(content=content, task=task,
                                              user=user, stat=state)
            print("post " + str(post.id))
            post_url.is_ready = True
            post_url.added_date = timezone.now()
        except Exception as e:
            if "Содержание не найдено" in res:
                post_url.is_successful = False
            elif "Вход на Facebook | Facebook" in res:
                print("sleep proxy")
            else:
                print(e)
        post_url.is_parsing = False
        post_url.save()


@app.task
def update_proxy():
    print("update_proxy")
    key = models.Keys.objects.all().first().proxykey
    # &country=ru
    new_proxy = requests.get(
        "https://api.best-proxies.ru/proxylist.json?key=%s&type=http,https&speed=1,2" % key,
        timeout=60)
    proxies = []
    limit = 0
    for proxy in json.loads(new_proxy.text):
        host = proxy['ip']
        port = proxy['port']
        print(host)
        print(port)

        session = generate_proxy_session('test', 'test', host, port)
        if not models.Proxy.objects.filter(host=host, port=port).exists():
            if check_facebook_url(session):
                if port == '8080':
                    if check_proxy_available_for_facebook(session):
                        models.Proxy.objects.create(host=host, port=port, login="test", password="test")
                else:
                    models.Proxy.objects.create(host=host, port=port, login="test", password="test")
    #                     proxies.append(models.Proxy(host=host, port=port, login="test", password="test"))
    #     limit += 1
    #     if limit >= 10:
    #         limit = 0
    #         models.Proxy.objects.bulk_create(proxies, batch_size=200, ignore_conflicts=True)
    #         proxies = []
    # models.Proxy.objects.bulk_create(proxies, batch_size=200, ignore_conflicts=True)


def generate_proxy_session(proxy_login, proxy_password, proxy_host, proxy_port):
    session = requests.session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (X11; Linux i686; rv:39.0) Gecko/20100101 Firefox/39.0'
    })
    proxy_str = f"{proxy_login}:{proxy_password}@{proxy_host}:{proxy_port}"
    proxies = {'http': f'http://{proxy_str}', 'https': f'https://{proxy_str}'}

    session.proxies.update(proxies)
    return session


def check_facebook_url(session):
    try:
        response = session.get('https://m.facebook.com', timeout=15)
        if response.ok:
            return True
    except Exception as e:
        print(e)
        pass
    return False


def check_proxy_available_for_facebook(session):
    try:
        accounts = models.Account.objects.filter(banned=False).order_by('id')[:500]
        account = random.choice(accounts)
        # login = "+79910404158"
        # password = "yBZHsBZHou761"
        print(account.id)
        response = session.post('https://m.facebook.com/login.php', data={
            'email': account.login,
            'pass': account.password,
            # 'email': login,
            # 'pass': password
        }, allow_redirects=False, timeout=10)
        start_page = session.get('https://www.facebook.com/', timeout=10)
        print(start_page)
        if 'login/?privacy_mutation_token' in start_page.url:
            account.banned = True
            account.save()
            return check_proxy_available_for_facebook(session)
        if 'checkpoint' not in start_page.url and '/login/device-based/regulr/' not in start_page.url:
            print(str(account.id) + " ok")
            return True
    except Exception as e:
        print(e)
        pass
    print(str(account.id) + " bad")

    return False


@app.task
def delete_bad_worker_credentials():
    print("delete")
    for cred in models.WorkCredentials.objects.filter(locked=True):
        try:
            # if proxy.login == "sergmga_gmail_com" or \
            #         not check_proxy("http://www.zahodi-ka.ru/proxy/check/?p=http://%s:%s" % (proxy.host,
            #                                                                                  str(proxy.port))):
            account = cred.account
            account.available = False
            account.banned = False
            account.save()
            #     proxy.available = False
            #     proxy.save()
            cred.delete()
        except Exception:
            pass


@app.task
def check_not_available_accounts():
    # maybe 100 ??
    # [:500]
    for account in models.Account.objects.filter(available=False).order_by("-id")[:500]:
        print("account.id")
        print(account.id)
        check_accounts(account, attempt=0)


def check_proxy(url, attempt=0):
    if '<ok>' in requests.get(url, timeout=60).text:
        print("check_proxy True " + str(attempt))
        return True
    else:
        print("check_proxy False " + str(attempt))
        if attempt >= 5:
            return False
        else:
            return check_proxy(url, attempt + 1)

    # TEST PROXY
    # res_er = requests.get("http://www.zahodi-ka.ru/proxy/check/?p=http://181.118.145.146:9991")
    # res_ok = requests.get("http://www.zahodi-ka.ru/proxy/check/?p=http://181.118.145.146:999")
    #
    # if '<er>' in res_er.text:
    #     print("res_er bad")
    # if '<ok>' in res_er.text:
    #     print("res_er ok")
    # if '<er>' in res_ok.text:
    #     print("res_ok bad")
    # if '<ok>' in res_ok.text:
    #     print("res_ok ok")

    # queryset._raw_delete(queryset.db)


def get_available_proxy():
    proxies = models.WorkCredentials.objects.all().values_list('proxy', flat=True)
    proxy = models.Proxy.objects.filter(available=True) \
        .exclude(id__in=proxies).order_by(
        # "attempts").first()
        "last_time_checked").last()
    if proxy is None:
        proxy = models.Proxy.objects.filter(available=True) \
            .order_by(
            # "attempts").first()
        "last_time_checked").last()
    print("proxy.id")
    print(proxy.id)
    if proxy is not None:
        try:
            print("sessin")
            session = generate_proxy_session(proxy.login, proxy.password, proxy.host, proxy.port)
            if check_facebook_url(session):
                print("ok")
                proxy.last_time_checked=datetime.now()
                proxy.save()
                return proxy
        except Exception as e:
            pass
        try:
            proxy.delete()
        except Exception as e:
            proxy.available = False
            proxy.save()

        return get_available_proxy()
        # else:
        #     return get_available_proxy()
    else:
        return None


def check_accounts(account, attempt=0):
    email = account.login
    password = account.password
    session = requests.session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (X11; Linux i686; rv:39.0) Gecko/20100101 Firefox/39.0'
    })

    proxy = get_available_proxy()
    if proxy is None:
        return

    try:
        session = generate_proxy_session(proxy.login, proxy.password, proxy.host, proxy.port)
        response = session.get('https://m.facebook.com', timeout=10)

        # login to Facebook
        response = session.post('https://m.facebook.com/login.php', data={
            'email': email,
            'pass': password
        }, allow_redirects=False)

        # If c_user cookie is present, login was successful
        print("check cookies")
        if response.ok:
            if 'c_user' in response.cookies:
                start_page = session.get('https://www.facebook.com/')
                if 'checkpoint' not in start_page.url:
                    print("account ok " + email)
                    account.available = True
                    account.banned = False
                    account.save()
                    try:
                        models.WorkCredentials.objects.create(account=account, proxy=proxy, locked=False,
                                                              user_agent=models.UserAgent.objects.filter(supported=True)
                                                              .order_by('?').first()
                                                              )
                    except Exception:
                        print("cannot create WorkCredentials ")
                    return True
                print("account disable " + email)
            else:
                account.banned = False
                account.save()
        return False
    except Exception:
        proxy.available = False
        proxy.save()
        if attempt < 5:
            print("account Exception " + email)

            return check_accounts(account, attempt + 1)
        else:
            print("account Exception disable " + email)
            return False


@app.task
def delete_old_proxy():
    for proxy in models.Proxy.objects.filter(expirationDate__lte=datetime.now()):
        try:
            if not models.WorkCredentials.objects.filter(proxy=proxy, locked=False).exists():
                proxy.delete()
        except Exception:
            pass


@app.task
def update_task():
    tasks = [
        3635,
        11120,
        11117,
        11116,
        11040,
        11039,
        11038,
        11035,
        10890,
        10889,
        10888,
        10887,
        10886,
        10885,
        10884,
        10883,
        10882,
        10881,
        10880,
        6222
    ]
    for task in tasks:
        try:
            task = models.Task.objects.get(id=task)
            task.status=None
            task.finish_time=None
            task.save(update_fields=["status", "finish_time"])
        except Exception:
            pass
