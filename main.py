import requests
import sqlite3
import json
from bs4 import BeautifulSoup
import pandas as pd
dfru = pd.read_csv('FakeNameRU.csv')
dfen = pd.read_csv('FakeNameEN.csv')
rumalenames = set(dfru[dfru['Gender'] == 'male']['GivenName'])
rufemalenames = set(dfru[dfru['Gender'] == 'female']['GivenName'])
enmalenames = set(dfen[dfen['Gender'] == 'male']['GivenName'])
enfemalenames = set(dfen[dfen['Gender'] == 'female']['GivenName'])
def get_html(url, params=None):
    r = requests.get(url, params=params)
    return r.text  
def get_in(html_product,text):
    index_data_begin = html_product.find(text)
    counter_open = 0
    counter_end = 0
    data_product = ''
    for index_str in range(index_data_begin+len(text)-1,len(html_product)):
        data_product = data_product + html_product[index_str]
        if(html_product[index_str]=='{'):
            counter_open+=1
        if(html_product[index_str]=='}'):
            counter_end+=1
        if(counter_open==counter_end and counter_open!=0):
            break
    return data_product
def scrolling_states(URL,states_local_url):
    html = get_html(URL)
    json_html = json.loads(html)
    try:
        items = json_html["items"]
        next_url = json_html['more']['link']
        for item in items:
            try:
                link = item['rawItem']["share_link"]
                if(link.find('zen.yandex.ru/media')!=-1):
                    states_local_url.append(item['rawItem']["share_link"])
            except:
                try:
                    link = item["share_link"]
                    if(link.find('zen.yandex.ru/media')!=-1):
                        states_local_url.append(item["share_link"])
                except:
                    print('Error')
        return scrolling_states(next_url,states_local_url)
    except:
        print('Статьи закончились')
        return states_local_url
def parse_states(href):
    states_local_url = list()
    data_main_json = get_in(get_html(href),'"exportData":{')
    data_main_json = json.loads(data_main_json)
    items = data_main_json["items"]
    for item in items:
        try:
            link = item['rawItem']["share_link"]
            if(link.find('zen.yandex.ru/media')!=-1):
                states_local_url.append(item['rawItem']["share_link"])
        except:
            try:
                link = item["share_link"]
                if(link.find('zen.yandex.ru/media')!=-1):
                    states_local_url.append(item["share_link"])
            except:
                print('Error')
    next_url = data_main_json['more']['link']
    return scrolling_states(next_url,states_local_url)
def answer(URL):
    publication_id = URL.split('-')
    publication_id = publication_id[-1]
    html_stats = 'https://zen.yandex.ru/media-api/publication-view-stat?publicationId='+str(publication_id)
    html_stats = get_html(html_stats)
    json_stats = json.loads(html_stats)
    views = json_stats['views'] #                               число просмотров!!!
    viewsTillEnd = json_stats['viewsTillEnd'] #                число дочитываний!!!
#    comments = json_stats['comments'] 
    html = get_html(URL)
    json_html = json.loads(get_in(html,'w._data = {'))
    tags = []
    for tag in json_html["publication"]["tags"]:
        tags.append(tag['title'])
    ownerUid = json_html['publisher']['ownerUid']
    publisherId = json_html['publisher']['id']
    documentID = 'native%3A'+publication_id
    url_comments = f'https://zen.yandex.ru/api/comments/top-comments?withUser=true&publisherId={publisherId}&documentId={documentID}&channelOwnerUid={ownerUid}'
    html_comments = get_html(url_comments)
    json_comments_main = json.loads(html_comments)
    publicationLikeCount = json_comments_main['publicationLikeCount'] #    число лайков!!!
    comments_counter = len(json_comments_main['comments']) #    число комментариев!!!
    max_path = 0 #                                      максимальное число ответов!!!
    female_counter_comment = 0
    male_counter_comment = 0
    for comment in json_comments_main['comments']:
        commentid = comment['id']
        url_comment = f'https://zen.yandex.ru/api/comments/child-comments/{commentid}?publisherId={publisherId}&documentId={documentID}&channelOwnerUid={ownerUid}'
        html_comment = get_html(url_comment)
        json_comment = json.loads(html_comment)
        try:
            comments_counter+=len(json_comment['comments'])
            max_path = max(max_path,len(json_comment['comments']))
        except:
            print('нет комментов ответных(')
    for author in json_comments_main['authors']:
        try: 
            name = author['firstName']
            if name in rumalenames:
                male_counter_comment+=1
            if name in enmalenames:
                male_counter_comment+=1
            if name in rufemalenames:
                female_counter_comment+=1
            if name in enfemalenames :
                female_counter_comment+=1
        except:
            try:
                name = author['displayName']
                name = name.split()
                name = name[0]
                if name in rumalenames:
                    male_counter_comment+=1
                if name in enmalenames:
                    male_counter_comment+=1
                if name in rufemalenames:
                    female_counter_comment+=1
                if name in enfemalenames :
                    female_counter_comment+=1
            except:
                continue
    soup = BeautifulSoup(html,'lxml')
    all_text = soup.find_all('p')
    title = soup.find('h1',class_='article__title article__title_layout_redesign article__title_theme_undefined article__title_text-styling_redesign').text #название статьи!!!!
    date_posting = soup.find('div',class_='article-stats-view-redesign__date').text #        время постинга!!!!
    html_text = soup.find('div',class_='article__middle article__middle_layout_redesign article__middle_theme_undefined article__middle_text-styling_redesign')
    href_text_all = html_text.find_all(href=True) # все блоки которые имеют ссылки
    img_all = html_text.find_all('img') # все html фоток           
    video_all = html_text.find_all('iframe')         
    image_hrefs = set() #                                          ссылки на фотографии из статьи!!!!
    video_hrefs = set() #                                          ссылки на видео из статьи!!!!
    for video in video_all:
        if(video.get('data-src')==None):
            video_hrefs.add(video.get('src'))
        else:
            video_hrefs.add(video.get('data-src'))
    for img in img_all:
        if(img.get('data-src')==None):
            image_hrefs.add(img.get('src'))
        else:
            image_hrefs.add(img.get('data-src'))
    count_image = len(image_hrefs) #                                              число фотографий!!!!
    count_video = len(video_hrefs)
    set_hrefs_all = set() #                                               ссылки на другие ресурсы!!!!
    yandex_dzen = set() #                                                      другие статьи дзена!!!!
    for href_text in href_text_all:
        href_in_text =  href_text.get('href')
        if(href_in_text.find('zen.yandex.ru/media')!=-1):
            yandex_dzen.add(href_in_text)
        else:
            set_hrefs_all.add(href_in_text)
    simbols_count = 0 #                                                 количество символов статьи!!!!
    for textik in all_text:
        if(textik.text!=''):
            simbols_count = simbols_count+len(textik.text)
    likes_dict = dict()
    female_counter_like = 0
    male_counter_like = 0
    for index in range(0,10000,100):
        URL_likes = f'https://zen.yandex.ru/api/comments/document-likers/native:{publication_id}?offset={index}&limit=100&publisherId={publisherId}&documentId={documentID}&channelOwnerUid={ownerUid}'    
        html_likes = get_html(URL_likes)
        json_likes = json.loads(html_likes)
        if(len(json_likes['usersInterests'])==0):
            break
        for interes_user in json_likes['usersInterests']:
            for interes in interes_user['interests']:
                try:
                    likes_dict[interes['title']]=likes_dict[interes['title']]+1
                except:
                    likes_dict[interes['title']]=1
        for user_info in json_likes['users']:
            try: 
                name = user_info['firstName']
                if name in rumalenames:
                    male_counter_like+=1
                if name in enmalenames:
                    male_counter_like+=1
                if name in rufemalenames:
                    female_counter_like+=1
                if name in enfemalenames :
                    female_counter_like+=1
            except:
                try:
                    name = user_info['displayName']
                    name = name.split()
                    name = name[0]
                    if name in rumalenames:
                        male_counter_like+=1
                    if name in enmalenames:
                        male_counter_like+=1
                    if name in rufemalenames:
                        female_counter_like+=1
                    if name in enfemalenames :
                        female_counter_like+=1
                except:
                    print('Cтранный какой-то')
    list_d = list(likes_dict.items())
    list_d.sort(key=lambda i: i[1])
    try:
        top_one = list_d[-1]
    except:
        top_one = None
    try:    
        top_two = list_d[-2]
    except:
        top_two = None
    try:
        top_three = list_d[-3]
    except:
        top_three = None
    try:
        top_four = list_d[-4]
    except:
        top_four = None
    try:
        top_five = list_d[-5]
    except:
        top_five = None
    if(top_one == None):
        interes_top = 'Ни у кого нет интересов'
    elif(top_two==None):
        interes_top = top_one[0]+' '+str(top_one[1])
    elif(top_three==None):
        interes_top = top_one[0]+' '+str(top_one[1])+', ' + top_two[0]+' '+str(top_two[1])
    elif(top_four==None):
        interes_top = top_one[0]+' '+str(top_one[1])+', ' + top_two[0]+' '+str(top_two[1])+', '+ top_three[0]+' '+str(top_three[1])
    elif(top_five==None):
        interes_top = top_one[0]+' '+str(top_one[1])+', ' + top_two[0]+' '+str(top_two[1])+', '+ top_three[0]+' '+str(top_three[1])+', '+ top_four[0]+' '+str(top_four[1])
    else:
        interes_top = top_one[0]+' '+str(top_one[1])+', ' + top_two[0]+' '+str(top_two[1])+', '+ top_three[0]+' '+str(top_three[1])+', '+ top_four[0]+' '+str(top_four[1]) +', '+top_five[0]+' '+str(top_five[1])
    if(len(tags)==0):
        tags='Ничего'
    if(len(image_hrefs)==0):
        image_hrefs='Ничего'
    if(len(video_hrefs)==0):
        video_hrefs='Ничего'
    return title,str(tags),date_posting,views,viewsTillEnd,publicationLikeCount,comments_counter,max_path,count_image,str(image_hrefs),count_video,str(video_hrefs),female_counter_like,male_counter_like,interes_top,female_counter_comment,male_counter_comment,len(yandex_dzen),str(yandex_dzen),len(set_hrefs_all),simbols_count
if __name__ == '__main__':
    print('Введите название БД')
    name_of_basedata = input()
    db = sqlite3.connect(f'{name_of_basedata}.db')
    sql = db.cursor()
    sql.execute("""CREATE TABLE IF NOT EXISTS states (
        name_of_state TEXT,        
        tag_state TEXT,
        time_post TEXT,
        seen_counter TEXT,
        readings_counter TEXT,
        like_counter TEXT,
        comment_counter TEXT,
        max_answer_comment TEXT,
        photo_counter TEXT,
        href_photo TEXT,
        href_video_counter TEXT,
        href_video TEXT,
        likes_from_female TEXT,
        likes_from_male TEXT,
        interes TEXT,
        comment_from_female TEXT,
        comment_from_male TEXT,
        dzen_href_counter TEXT,
        yandex_dzen_href TEXT,
        another_href_counter TEXT,
        symbols_counter TEXT
    )""")
    db.commit()
    with open('url_states.txt', 'r',encoding='utf-8') as f:
        url_states = f.read()
    url_states = url_states.split()
    for url in url_states:
        url2_states = parse_states(url)
        for url2 in url2_states:
            try:
                title,tags,date_posting,views,viewsTillEnd,publicationLikeCount,comments_counter,max_path,count_image,image_hrefs,count_video,video_hrefs,female_counter_like,male_counter_like,interes_top,female_counter_comment,male_counter_comment,yandex_dzen,yandex_dzen_href,set_hrefs_all,simbols_count = answer(url2)
                sql.execute(f"INSERT INTO states VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",(title,tags,date_posting,views,viewsTillEnd,publicationLikeCount,comments_counter,max_path,count_image,image_hrefs,count_video,video_hrefs,female_counter_like,male_counter_like,interes_top,female_counter_comment,male_counter_comment,yandex_dzen,yandex_dzen_href,set_hrefs_all,simbols_count))
                db.commit()
            except:
                continue