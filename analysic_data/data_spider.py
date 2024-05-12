
import urllib.request
from lxml import etree
import pymongo
import time
import threading
import multiprocessing
from multiprocessing import Pool
from multiprocessing import Process,Queue
from multiprocessing import cpu_count

'''
爬虫获取数据
'''

class Spider:
    def __init__(self):
        self.conn = pymongo.MongoClient("127.0.0.1",27017)
        # self.db = self.conn['medical']##建立数据库
        # self.col = self.db['data']##建表，字典形式
        self.db = self.conn['all_medical']  ##建立数据库
        self.col = self.db['data']  ##建表，字典形式

    def html_analysis(self,url,tag):
        headers={'User-Agent' : 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                 'Chrome/99.0.4844.51 Safari/537.36'}
        req=urllib.request.Request(url=url,headers=headers)
        res=urllib.request.urlopen(req)
        html=res.read().decode(tag)
        return html
    # def html_analysis_utf(self,url):
    #     headers={'User-Agent' : 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
    #              'Chrome/99.0.4844.51 Safari/537.36'}
    #     req=urllib.request.Request(url=url,headers=headers)
    #     res=urllib.request.urlopen(req)
    #     html=res.read().decode('utf-8')
    #     return html

    def spider_main(self, start, end):
        for page in range(start, end):
            try:
                basic_url = 'http://jib.xywy.com/il_sii/gaishu/%s.htm' % page
                cause_url = 'http://jib.xywy.com/il_sii/cause/%s.htm' % page
                prevent_url = 'http://jib.xywy.com/il_sii/prevent/%s.htm' % page
                symptom_url = 'http://jib.xywy.com/il_sii/symptom/%s.htm' % page
                inspect_url = 'http://jib.xywy.com/il_sii/inspect/%s.htm' % page
                treat_url = 'http://jib.xywy.com/il_sii/treat/%s.htm' % page
                food_url = 'http://jib.xywy.com/il_sii/food/%s.htm' % page
                drug_url = 'http://jib.xywy.com/il_sii/drug/%s.htm' % page
                hospital_url = 'http://jib.xywy.com/il_sii/doctor/%s.htm' % page
                data = {'basic_info': self.basic_info_analysis(basic_url),
                        'cause_info': self.more_spider(cause_url),
                        'prevent_info': self.more_spider(prevent_url),
                        'symptom_info': self.more_spider(symptom_url),
                        'inspect_info': self.more_spider(inspect_url),
                        'treat_info': self.treat_spider(treat_url),
                        'food_info': self.food_spider(food_url),
                        'drug_info': self.drug_spider(drug_url),
                        'hospital': self.hospital_spider(hospital_url)}
                self.col.insert_one(data)
                print("Page processed:", page)
            except Exception as e:
                print(e, page)


    def hospital_spider(self,url):
        html = self.html_analysis(url,"gbk")
        hospital=etree.HTML(html)
        hospital=[i.xpath('string(.)') for i in hospital.xpath('//div[@class="panels"]/div[17]/div/div/p[2]')]
        return hospital

    def drug_spider(self,url):
        html=self.html_analysis(url,"gbk")
        drug_info=etree.HTML(html)
        drug_info=drug_info.xpath('//div[@class="fl drug-pic-rec mr30"]/p/a')
        drug_dict={}
        for drug in drug_info:
            drug_name="".join(drug.xpath('text()')).replace("\n","").replace(" ","")
            drug_url=drug.xpath('@href')[0]
            html=self.html_analysis(drug_url,"utf-8")
            drug_desc=etree.HTML(html)
            drug_spend=[ i.xpath('string(.)') for i in drug_desc.xpath('//div[@class="d-info-dl mt5"]/dl[2]/dd')]
            drugs_gongneng = [i.xpath("string(.)").replace("\r","").replace("\n","")
                              for i in drug_desc.xpath('//div[@class="d-tab-inf"]/dl[3]/dd')]
            drugs_use =[i.xpath("string(.)").replace("\r","").replace("\n","").replace("\u3000","")
                        for i in drug_desc.xpath('//div[@class="d-tab-inf"]/dl[4]/dd')]
            drug_dict[drug_name]={"功能主治":drugs_gongneng,"用法用量":drugs_use,"价格":drug_spend}
        # drug_info_name=[i.replace("\n","").replace(" ","")for i in drug_info.xpath('//div[@class="fl drug-pic-rec mr30"]/p/a/text()')]
        # drug_url=drug_info.xpath('//div[@class="fl drug-pic-rec mr30"]/p/a/@href')
        # print(drug_info_name)
        # drug_desc={}
        # for i in range(len(drug_info_name)):
        #     drug_desc[drug_info_name[i]]=drug_url[i]
        # print(drug_desc)
        # for i in range(len(drug_info_name)):
        #     html2=self.html_analysis_utf(drug_url[i])
        #     drugs=etree.HTML(html2)
        #     drugs_gongneng=drugs.xpath('//div[@class="d-tab-inf"]/dl[3]/dd')
        #     drugs_use=drugs.xpath('//div[@class="d-tab-inf"]/dl[4]/dd')
        #     for durg_gongneng in drugs_gongneng:
        #         durg_gongneng=durg_gongneng.xpath('string(.)')
        #         print(durg_gongneng)
        #     for drug_use in drugs_use:
        #         drug_use=drug_use.xpath('string(.)')
        #         print(drug_use)
        return drug_dict

    '''基本信息解析'''
    def basic_info_analysis(self,url):
        html=self.html_analysis(url,"gbk")
        info_html=etree.HTML(html)
        title=info_html.xpath("//title/text()")#药物名称
        desc=info_html.xpath('//div[@class="jib-articl-con jib-lh-articl"]/p/text()')#疾病简介
        desc="".join(desc).replace("\r","").replace("\n","").replace("\t","").replace(" ","")#疾病简介,简介中有特殊转义字符去除
        basic_knowledge=info_html.xpath('//div[@class="mt20 articl-know"]/p')#基本信息
        information = []
        for basic in basic_knowledge:
            info=basic.xpath("string(.)").replace("\r","").replace("\n","").replace("\t","").replace("\xa0"," ").replace("   ","")
            information.append(info)
        basic_data={}
        basic_data['name']=title[0].split('的简介')[0]
        basic_data["desc"]=desc
        for i in information:
            i=i.split("：")
            if len(i) !=1:
                basic_data[i[0]]=i[1]
        return basic_data

    """  通用于病因,预防,症状,检查方法爬取 """
    def more_spider(self,url):
        html=self.html_analysis(url,"gbk")
        more_info=etree.HTML(html)
        more_info=more_info.xpath('//div[@class="jib-janj bor clearfix"]/div/p')
        more_information=[]
        for info in more_info:
            info=info.xpath('string(.)').replace("\n","").replace("\t","").replace("\r","").replace(" ","")
            if info:
                more_information.append(info)
        return "\n".join(more_information)

    """ 治疗方案爬取"""
    def treat_spider(self,url):
        html = self.html_analysis(url,"gbk")
        treat_info=etree.HTML(html)
        treat_info=treat_info.xpath('//div[@class="jib-lh-articl"]/p')
        treat_inforation=[]
        for info in treat_info:
            info=info.xpath('string(.)').replace("\n","").replace("\t","").replace("\r","").replace(" ","")
            if info:
                treat_inforation.append(info)
        return "\n".join(treat_inforation)

    """ 饮食保健，益吃，忌吃食物爬取"""
    def food_spider(self,url):
        html=self.html_analysis(url,"gbk")
        food_info=etree.HTML(html)
        food_command=food_info.xpath('//div[@class="diet-item"]/p')#饮食保健
        food_command_list=[]
        for info in food_command:
            info=info.xpath('string(.)').replace("\n","").replace("\t","").replace("\r","").replace(" ","")
            if info:
                food_command_list.append(info)
        food_command="\n".join(food_command_list)
        info_eat=food_info.xpath('//div[@class="diet-img clearfix mt20"]')
        try:
            food = {}
            # 推荐食谱
            food['good_cooking_reconmand']="".join(food_command)+"\n推荐以下食疗："+",".join(info_eat[2].xpath('./div/p/text()'))
            # 宜吃食物
            food['good_eat']=",".join(info_eat[0].xpath('./div/p/text()'))
            # 忌吃食物
            food['bad_eat']=",".join(info_eat[1].xpath('./div/p/text()'))
        except:
            food['good_cooking_reconmand']="".join(food_command)
            return food
        return food


def run_spider(start, end):
    spider = Spider()
    spider.spider_main(start, end)


if __name__ == '__main__':
    # 设定页面和进程数
    total_pages = 10130    # 网站总数：10137
    num_processes = 8  # 可以设置为 CPU 核心数(4核，1核可能可以超频处理两线程，最多是8，但是cpu占用还是低，可能因为网络等原因没有完全利用线程，试试设高点)

    # 计算每个进程应处理的页面数
    pages_per_process = total_pages // num_processes

    # 创建进程池
    with Pool(processes=num_processes) as pool:
        pool.starmap(run_spider, [(i * pages_per_process, (i + 1) * pages_per_process) for i in range(num_processes)])