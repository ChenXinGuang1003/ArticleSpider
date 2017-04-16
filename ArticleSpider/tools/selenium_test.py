from selenium import webdriver
import time

# 设置浏览器不加载图片
chrome_opt = webdriver.ChromeOptions()
prefs = {'profile.managed_default_content_settings.images': 2}
chrome_opt.add_experimental_option('prefs', prefs)

browser = webdriver.Chrome(executable_path="C:/Users/shishengjia/PycharmProjects/chromedriver_win32/chromedriver.exe",
                           chrome_options=chrome_opt)


# # 模拟登陆微博
# browser.get("http://www.weibo.com/")
#
# # 等待10秒，等待页面全部加载完成
# time.sleep(10)
#
# browser.find_element_by_css_selector("#loginname").send_keys("13419516267")
# browser.find_element_by_css_selector(".info_list.password input[name='password']").send_keys("ssjusher123")
# browser.find_element_by_css_selector(".info_list.login_btn a[node-type='submitBtn']").click()

# 模拟鼠标下拉
browser.get("https://www.oschina.net/blog")
time.sleep(5)
for i in range(3):
    # 执行js代码模拟下拉动作
    browser.execute_script("window.scrollTo(0, document.body.scrollHeight); var lenofPage=document.body.scrollHeight; return lenofPage")
    time.sleep(3)

browser.quit()



