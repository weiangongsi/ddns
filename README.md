此项目为 [Home Assistant](https://www.home-assistant.io/) 的域名动态解析插件。

## 功能

将公网ip解析到阿里云或腾讯云。

[![hacs_badge](https://img.shields.io/badge/HACS-Default-41BDF5.svg?style=for-the-badge)](https://github.com/hacs/integration)

## 使用

    1. 在HACS中搜索 ddns安装，或者 clone 此项目, 将 custom\_components/ddns目录拷贝至 Home Assistant 配置目录的 custom\_components 目录下。
    2. 重启 Home Assistant 服务。
    3. 在 Home Assistant 的集成页面，搜索 "ddns" 并添加。
    4. 第一次添加组件由于安装阿里云依赖库比较慢，请耐心等待，然后根据提示填写表单。