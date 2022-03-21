import pandas as pd
from bs4 import BeautifulSoup
import requests
import re

wp_filetypes = 'https://en.wikipedia.org/wiki/List_of_file_formats'

page = requests.get(wp_filetypes)

soup = BeautifulSoup(page.text,'html.parser')

#idenfity the heading tags
#create dict to track starting line of each heading tag
heading_tags = ["h1", "h2", "h3","h4"]
heading_pos = [i.sourceline for i in soup.find_all(heading_tags)]
heading_text = [i.text for i in soup.find_all(heading_tags)]

#identify the content that we are interested in and the related links
#track the line positions of each

#text and position of content
content_pos = [i.sourceline for i in soup.find_all('li')]
content_text = [i.text for i in soup.find_all('li')]

#links
href_pos = [i.sourceline for i in soup.find_all('a',href=True)]
href_link = [i['href'] for i in soup.find_all('a',href=True)]

def get_tag_pos(poslist,contentlist):
    #construct a dict to hold the starting and ending line of each element you are processing
    #input: two lists of same length
    #output: dict of tuples with start and end pos
    poses = {}

    for item in range(len(contentlist)):
        begin = poslist[item]
        
        #create tuple with beginning and ending indexes of each heading
        if item == len(poslist)-1:
            end = content_pos[-1] #if end of heading list take last content tag pos
        else:
            end = poslist[item+1]-1  #next line minus 1
        
        poses[contentlist[item]] = (begin,end)

    return poses


heading_scope = get_tag_pos(heading_pos,heading_text)

content_scope = get_tag_pos(content_pos,content_text)

links_scope = get_tag_pos(href_pos,href_link)

def connect_links(content,links):
    #create dict to connect the text from list content 
    #to relevant tags
    #input: two dicts
    #output: nested dict
    content_links = {}

    for text in content:
        
        #nest dict holds the position of the content and the link
        temp = {}
        temp['pos'] = content[text]
        temp['link'] = []
                    
        for link in links:
            if content[text][0] <= links[link][0] <= content[text][1]:
                temp['link'].append(link)

        content_links[text] = temp
    
    return content_links

files_links = connect_links(content_scope,links_scope)

def join_hdr_content(hdr,content):
    #join the headers with the content (file types and links) based on position
    
    hdr_cont_out = dict(zip(hdr.keys(), ([] for _ in hdr.keys())))
    #hdr_cont_out_lnk = dict(zip(hdr.keys(), ([] for _ in hdr.keys())))

    for h in hdr:
        for c in content:
            #check if the file info tag is at the position of the heading
            if hdr[h][0] <= content[c]['pos'][0] <= hdr[h][1]:
                file_info = []
                file_info.append(c)
                
                if len(content[c]['link']) > 0:
                    file_info.append(content[c]['link'][0])
                else:
                    file_info.append(None)

                hdr_cont_out[h].append(file_info)

    
    #remove unneeded items in the final output
    return  {k: v for k, v in hdr_cont_out.items() if k.endswith('[edit]')}
    
    
final_dict = join_hdr_content(heading_scope,files_links)


def df_from_wpdict(wpdict):
    #create a dataframe for each item in a dict and append to a main df
    #dict -> df
    
    df_cols = ['file_category','file_info','wikilink']
    filetypes = pd.DataFrame(columns=df_cols)
    
    
    #loop through the dict items and append to the df
    for k in wpdict:
        for f in wpdict[k]:
            data = [k,f[0],f[1]]
            df = pd.DataFrame([data],columns=df_cols)
            filetypes = filetypes.append(df)
    
    return filetypes    

df_ft = df_from_wpdict(final_dict)

def clean_fc(value):
    #clean the text in file_category
    return value.replace('[edit]','')

def remove_elrf(df):
    #remove the headings that related to external links and references
    #in the wikipedia article
    return df[~df.file_category.isin(['External links','References','See also'])].reset_index().drop('index',axis=1)


df_ft.file_category = df_ft.file_category.apply(clean_fc)

df_ft_rm = remove_elrf(df_ft)


def clean_links(value):
    #clean up the wikipedia links to just include this from wikipedia
    if value:
        if '/wiki/' in value:
            return 'https://en.wikipedia.org/' + value
        else:
            return None

df_ft_rm.wikilink = df_ft_rm.wikilink.apply(clean_links)

def extract_file_ext(value):
    #extract a file extension from string
    if value:
        if '-' in value:
            return value.split('-')[0]
        if ' – ' in value:
            return value.split(' – ')[0]
        else:
            pass 
        
        
        #else:
        #    re.findall(r'\.\w+',value)[0].replace('.','')

df_ft_rm['file_ext'] = df_ft_rm.file_info.apply(extract_file_ext)

def re_filetypes(value):
    #function leverages re to pull 
    
    result_dot = re.findall(r'\.\w+',value)
    result_dot = [i.replace('.','') for i in result_dot]


    result_nodot = re.findall(r'\w{3,}',value)
    
    if len(result_dot) > 0:
        return result_dot

    elif len(result_nodot) > 0:
        return result_nodot[0]
        
    
def apply_re_ft(df):
    #apply the re filetypes and create new rows for each file extension
    #for one row of df
    filter_values = list(df.file_info)

    final_df = df.copy().truncate(after=0)

    for fi in filter_values:
        indf = df[df.file_info == fi]

        outdf = indf.copy()

        value = list(outdf.file_info)[0]
        
        ft_values =  re_filetypes(value)


        if ft_values:
            if  len(ft_values) > 1:
                
                for item in ft_values:
                    tempdf = outdf.copy()
                    tempdf.file_ext = item
                    outdf = outdf.append(tempdf)

                outdf =  outdf[outdf.file_ext.isna() == False]

            else:
                outdf.file_ext = ft_values[0]

        final_df = final_df.append(outdf)

    return final_df[final_df.file_ext.str.len() > 1].drop_duplicates()

    
df_out = apply_re_ft(df_ft_rm)

def final_output():
    return df_out