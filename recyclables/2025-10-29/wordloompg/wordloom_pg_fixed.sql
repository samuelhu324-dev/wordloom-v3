CREATE TABLE IF NOT EXISTS sources (
	id INTEGER NOT NULL, 
	name VARCHAR(255) NOT NULL, 
	url VARCHAR(1024), 
	PRIMARY KEY (id), 
	UNIQUE (name)
);
CREATE TABLE IF NOT EXISTS articles (
	id INTEGER NOT NULL, 
	title VARCHAR(255) NOT NULL, 
	source_id INTEGER, 
	created_at TIMESTAMP, 
	PRIMARY KEY (id), 
	FOREIGN KEY(source_id) REFERENCES sources (id)
);
CREATE TABLE IF NOT EXISTS entries (
	id INTEGER NOT NULL, 
	src_text TEXT NOT NULL, 
	tgt_text TEXT NOT NULL, 
	lang_src VARCHAR(8), 
	lang_tgt VARCHAR(8), 
	created_at TIMESTAMP, article_id INTEGER, position INTEGER, 
	PRIMARY KEY (id)
);
CREATE TABLE IF NOT EXISTS entry_sources (
	entry_id INTEGER NOT NULL, 
	source_id INTEGER NOT NULL, 
	PRIMARY KEY (entry_id, source_id), 
	FOREIGN KEY(entry_id) REFERENCES entries (id), 
	FOREIGN KEY(source_id) REFERENCES sources (id)
);

INSERT INTO articles (id,title,source_id,created_at) VALUES (1,'CITS 1401 Python - Lab 6 - Dictionaries and classes/objects',NULL,'2025-10-10 14:55:37.699846'),
 (2,'CITS 1003 Cybersecurity - Lab 10 - AI',8,'2025-10-10 15:41:36.974575'),
 (3,'MyBatch',7,'2025-10-13 06:24:18.514157'),
 (4,'OALD7-E&C',6,'2025-10-13 06:24:21.883841'),
 (5,'CITS 1401 Python - Lab 7 - Project 2 - XYZ Research Institute',10,'2025-10-14 15:27:11.420035');
INSERT INTO entries (id,src_text,tgt_text,lang_src,lang_tgt,created_at,article_id,position) VALUES (1,'We can use [memory forensics] to identify malware that may have been only [resident in] memory and never saved on disk. We can also use it for evidence as to the activities of a user at a given time.','我们可以使用[内存取证]去识别可能一直只[寄存于]内存，从不在硬盘上保存的恶意软件。我们也可以使用内存取证找关于在一个给定时间点一名用户活动的证据。','en','zh','2025-10-02 14:04:16.000000',NULL,NULL),
 (2,'We support [electronic discovery] for civil [litigators] by collecting traditional digital documents and email evidence from your client or [opposing party].','我们收集你的客户或者[反对方]的传统数字文档和电邮证据，就可以支持民事[诉讼律师][电子举证]。','en','zh','2025-10-04 02:25:44.000000',NULL,NULL),
 (3,'One case for the extension premise comes from advances in information technology','其中一个延展假定的情况出自信息技术方面的进步','en','zh','2025-10-06 01:40:14.000000',NULL,NULL),
 (4,'Whenever we [come up with] a computational product, that product [is soon afterwards obsolete] due to technological advances','每当我们[拿出]一个计算机上的产品，那个产品由于科技进步[不久之后就废弃了]','en','zh','2025-10-06 01:40:14.000000',NULL,NULL),
 (5,'We should expect [the same]to apply to AI','我们应该希望[同样的情况]适用于AI','en','zh','2025-10-06 01:40:14.000000',NULL,NULL),
 (6,'Soon after we have produced a human-level AI, we will produce an even more intelligent AI','不久后我们已经产出人类级别的AI了，我们就将产出一个更加聪明的AI：一个AI+','en','zh','2025-10-06 01:40:14.000000',NULL,NULL),
 (7,'Please [consult] the solution [given] for phase 2 of the project before attempting this quiz;
the solution can be found on LMS.','在尝试这个小测前，请[查阅]项目阶段2[给出的]解决方案；解决方案在LMS上可以找到。','en','zh','2025-10-06 09:50:30.000000',NULL,NULL),
 (8,'Select all appointment numbers (apptNo) from the Appointment table, and the dateAndStartingTime (display as ''appointment data and time''). Only select appointments that are on the 24th or the 26th day [of month].
Hint: you should use the strftime() function.','选中Appointment表格里的所有问诊编号（apptNo）和dateAndStartingTime（显示为''问诊数据和时间''）只选中在[每月]24日或者26日的问诊。
提示：你应该使用strftime()函数。','en','zh','2025-10-06 10:01:08.000000',NULL,NULL),
 (9,'Select the uniqueIdentifierCode, dateAndStartingTime, clientNumber, prescribedCode, description, and currentServiceFee from all of the required tables, utilizing a JOIN.
Hint 1 which of the above attributes are keys that are common between tables, and which are only found in specific tables? You will need to differentiate those that appear in multiple tables that you join.
Hint 2 You will need to use 4 tables.','运用了一次JOIN，就能选中所有需要的表格里的uniqueIdentifierCode、dateAndStartingTime、clientNumber、prescribedCode、description和currentServiceFee，。
Hint 1 以上的属性哪个是表格之间很常见的钥匙，而哪些只在具体的表格中找到。
Hint 2 你得要使用上4个表格。','en','zh','2025-10-06 10:34:17.000000',NULL,NULL),
 (10,'Select the title, personalName, familyName from the Doctor table and order by personalName in ascending order, and by familyName in descending order.','选中Doctor表格里的title、personalName、familyName，以升序order by（按排序）personalName，并以降序排序familyName。','en','zh','2025-10-06 11:18:05.000000',NULL,NULL),
 (11,'Count the total number of services offered (display as ''Total Services''), and calculate the average and total service fees (display as ''Avg. Service Fee'' and ''Total Service Fee''), from the Services table.','Count已提供服务的总数字（显示为''Total Services''）并算出average和total服务费用（显示为''Avg. Service Fee''和''Total Service Fee''）在Services表格里数和算。','en','zh','2025-10-06 11:23:03.000000',NULL,NULL),
 (12,'[For] each Doctor, find how many services they offer, and display the Doctor’s personalName and familyName, as well as the count of services offered (displayed as ''Service Count'').
Only [show] doctors who offer more than 2 services.
Hint: You will need to use the tables Doctor and Gives.
Hint 2: having [will be useful].','[算]每个医生，求出他们提供多少服务并显示Doctor的personalName和familyName，以及已提供服务的个数（显示为''Service Count''）。
只[写]提供两个以上服务的医生。
提示：你得要使用上表格Doctor和Gives。
提示2：having[会很有用]。','en','zh','2025-10-06 12:12:40.000000',NULL,NULL),
 (13,'Select the names of doctors who give a service that costs more than $160.
Hint: you will need to use sub queries','选中给出一个花费高于160刀的服务的医生的名称。
线索：你得要使用上子查询。','en','zh','2025-10-06 13:57:15.000000',NULL,NULL),
 (14,'Select the personalName and familyName of patients who have an appointment with a doctor that works in Room 4.
Hint: You can use sub queries or WHERE or JOIN.','选中与一名在Room 4工作的一位doctor有一次appointment的病人的personalName和familyName。
线索：你可以使用子查询或者WHERE或者JOIN。','en','zh','2025-10-06 14:14:30.000000',NULL,NULL),
 (15,'Create a view named CompletedInvoices that shows the uniqueInvoiceNumber, apptNo, relevantDate, and status, [for only completed (''C'') invoices].','创建一个命名为CompletedInvoices的一张view，写上[只有填完的（''C''）发票才适用的]uniqueInvoiceNumber, apptNo, relevantDate, and status。','en','zh','2025-10-06 14:44:27.000000',NULL,NULL),
 (16,'Select all patient''s clientNumber who have a Patient record but are NOT listed as a ResponsibleCustomer.','选中有一次Patient记录但没有列作一名ResponsibleCustomer的所有病人的clientNumber。','en','zh','2025-10-06 14:51:52.000000',NULL,NULL),
 (17,'Select all appointments apptNo, dataAndStartingTime and uniqueNumber (as ''Room Number'') that happened between ''2025-04-24'' and ''2025-04-27'' AND where the room number [is either] 2, 3, [or] 5.
Hint: you [will need to use] date() function.','选中在''2025-04-24'' 和 ''2025-04-27''之间进行AND其中房间编号[不是]2、[就是]3[就是]5的所有问诊apptNo、dataAndStartingTime和uniqueNumber（选为''Room Number''）
提示：你[得要使用上]date()函数。','en','zh','2025-10-06 20:42:41.000000',NULL,NULL),
 (18,'[AI] A VIEW in SQL is like a virtual table - it doesn’t store data itself, but it [shows] data that comes from one or more real tables through a saved query','SQL中一次VIEW像是一张虚拟表，表没储存数据本身，但表[上面有]透过一个保存的查询来自一个或多个真实表格的数据','en','zh','2025-10-06 21:41:10.000000',NULL,NULL),
 (19,'[AI] You can think of it as a stored SELECT statement [with a name]','你可以把表想成是一个[有名字的]、SELECT储存语句','en','zh','2025-10-06 21:41:10.000000',NULL,NULL),
 (20,'[AI] The database will then run the original query [behind the scenes], [pulling] the latest data from the underlying tables','数据库然后将[拉出]底层表格里的最新数据，就能[在幕后]运行原始查询','en','zh','2025-10-06 21:41:10.000000',NULL,NULL),
 (21,'This lab will be using [live] malware samples','这个Lab将会使用[实时]恶意软件样本','en','zh','2025-10-07 10:33:30.000000',2,1),
 (22,'Although the samples we use [are not capable of] [breaking out] of docker containers, it is best [to minimize the risk] by doing this lab within a virtual machine (VM), such as using VirtualBox with Ubuntu or Kali Linux','尽管我们使用的样本[没有能力][打破]docker匣子，但最好在虚拟机之中做这个Lab（譬如说用Ubuntu或者Kali Linux使用VirtualBox）就可以[把风险降到最低]','en','zh','2025-10-07 10:33:30.000000',2,4),
 (23,'Please check the Setting up VM for labs sections','你在你的主机机械里直接在做Lab的话，一旦你已经做完Lab去移除所有恶意样本了，你应该删除匣子，否则你的杀毒软件可能很不高兴并发脾气','en','zh','2025-10-07 10:33:30.000000',2,2),
 (24,'If you are doing the lab directly from your host machine, you should delete the container once your have finished the lab to remove all malware samples - otherwise your antivirus software may not be happy and throw a tantrum','你运行匣子的时候可以添加--rm旗子就可以自动地删除匣子','en','zh','2025-10-07 10:33:30.000000',2,3),
 (25,'Artificial intelligence is [a collection of] technologies that allows computers to [simulate] human intelligence','人工智能是让电脑可以[模拟]人类智能的[一组]科技','en','zh','2025-10-07 11:26:14.000000',2,5),
 (26,'Its applicability in cybersecurity involves [all aspects of] AI, including natural language processing, [speech recognition], expert systems, robotics and vision','在网络安全中智能的适用性涉及AI的[方方面面]，包括自然语言处理、[语音识别]、专家系统、机器人与视觉','en','zh','2025-10-07 11:26:14.000000',2,6),
 (27,'[Fundamental to these types of AI is] machine learning, a technology that uses an approach to learning that tries and mimics the way [nerve cells] work in the brain','[对这些类型的AI密不可分的是]机械学习，是使用尽可能模仿大脑中[神经细胞]怎么工作的一类学习措施的一种科技','en','zh','2025-10-07 11:26:14.000000',2,7),
 (28,'One area of [active] research in machine learning is the use of [adversarial images]','机械学习的[热门]研究，其中一个领域是对[对抗图片]的使用','en','zh','2025-10-07 12:49:52.000000',2,8),
 (29,'This is where slight changes in the image causes machine learning systems to incorrectly classify objects within the image','这是轻轻在图片上改在图像内就造成机械学习系统去不正确地分类对象','en','zh','2025-10-07 12:49:52.000000',2,9),
 (30,'So for example, a panda is wrongly recognised as a [gibbon]','所以比如说，一只熊猫错误地识别为一只[长臂猿]','en','zh','2025-10-07 12:49:52.000000',2,10),
 (31,'[The changes to the image can be imperceptible to a human] and so this type of attack could be used to alter a [radiological image] and change [a negative diagnosis of cancer] to a positive one in a system that is automatically [screening for] cancer','[图像的更改一名人类可以察觉不到]，并且这类型的攻击能够使用去改动一张[放射图片]，在自动地[筛查]癌症的系统中把[对癌症的一次阴性诊断]改为一次阳性诊断','en','zh','2025-10-07 12:49:52.000000',2,11),
 (32,'Adversarial attacks [could] become increasingly common as we [come to] rely on machine learning systems to automate processes and decisions','由于我们[去]依赖机械学习系统去自动化进程和决策，对抗攻击[说不定]变得日益常见','en','zh','2025-10-07 16:38:01.000000',2,12),
 (33,'This [has made] the field of [research into] [defences against this type of attack] [important]','这[使得][对于][防御这类型攻击][的研究]领域[变得重要起来]','en','zh','2025-10-07 16:38:01.000000',2,13),
 (34,'In the area of malware recognition, malware can adopt tactics to prevent from recognition by taking an adversarial approach','在恶意软件识别领域，恶意软件可以采取对抗措施，就可以采用策略去阻止识别','en','zh','2025-10-07 16:38:01.000000',2,14),
 (35,'To [see how this works], we can use a program that uses what is called a non-targeted black box approach to adversarial images','要[懂这怎么用]，我们可以使用使用解决对抗图像所谓的非目标黑盒子措施的一个程序','en','zh','2025-10-07 16:38:01.000000',2,15),
 (36,'To set it up, follow the instructions below','要把程序安装上，按照以下的指示','en','zh','2025-10-07 16:38:01.000000',2,16),
 (37,'Also install matplotlib inside the container to run the code later','并安装匣子里面的matplotlib去运行之后的代码：一旦在docker匣子上，[还没有]转的话就转到目录/opt','en','zh','2025-10-07 16:42:45.000000',2,17),
 (38,'Once on the docker container, go to the directory /opt if [not already]','从那里运行exploit','en','zh','2025-10-07 16:42:45.000000',2,18),
 (39,'From there, run the exploit','py程序','en','zh','2025-10-07 16:42:45.000000',2,19),
 (40,'py program','这个程序将摄取一只拉布拉多一张正常的图像并创建对抗版的图像','en','zh','2025-10-07 16:42:45.000000',2,20),
 (41,'This program will take a normal image of a Labrador and create adversarial versions of the image','你对详细内容有兴趣的话，程序就来自一个叫做Foolbox的工具箱里','en','zh','2025-10-07 16:42:45.000000',2,21),
 (42,'To run the script, we [do so as follows]','要运行脚本，我们[如下这样做]：','en','zh','2025-10-07 16:45:18.000000',2,22),
 (43,'This takes the initial image of lab_og.jpg and then creates different versions of the image with the [perturbations] added. The script tests these images against the neural network and very quickly stops recognising a [Labrador] and starts recognising other dog types such as the [Saluki] and [Welmaraner], although note that [the levels of confidence] in that result are very low [~] 16%.s','这脚本取lab_og.jpg起初的图像，然后用已添加的[扰动]创建不同版本的图像。脚本针对神经网络测试这些图像并非常快就停止识别一只[拉布拉多]并开始识别其他狗类型，譬如[萨卢基]和[魏玛]，尽管注意到那个结果的[置信水平]非常低，[约]16%，[脚本也会识别]。','en','zh','2025-10-07 17:00:31.000000',2,23),
 (44,'After running the program, you should have some files','运行程序之后，你应该有一些文件：','en','zh','2025-10-07 17:07:50.000000',2,24),
 (45,'Copy these files to your host VM/machine (open up another terminal and use docker cp command)','把这些文件拷贝到你的主机VM/机械（再打开一个终端并使用docker cp命令）','en','zh','2025-10-07 17:09:03.000000',2,25),
 (46,'Note the Wolfram site [only works] [intermittently] - it isn''t reliable. If you can''t get it to work, don''t worry - just use the [predictions] that the program exploit.py printed out.','注意Wolfram网址[只能][断断续续][工作] - 不是很可靠。你不能让网址工作的话，就别担心 - 使用程序exploit.py打印出了的[预测值]就行了。','en','zh','2025-10-07 17:18:32.000000',2,26),
 (47,'Load the first image, Input.jpg into the site and verify that it is correctly recognised. Then try with [each of the other] adversarial images [starting with] Epsilon = 0.010.jpg and [going up]. If the site [errors out], wait a bit and then try again, it seems to not like images being loaded too quickly. Eventually, it should fail to recognise the last image (or [misclassify]) which [has had the most] perturbations applied to it.','把第一张图像Input.jpg加载进网址并核实图得到正确地识别。然后试试用[其他的每个以Epsilon = 0.010.jpg开头]的对抗图像并[升一升级]。网址[有错]的话，就等等然后再试一次，网址似乎不喜欢图片非常快被加载。最终，网址无法识别最后一张图（或者[错分]）已施加给图的扰动[是最多的]。','en','zh','2025-10-07 18:01:40.000000',2,27),
 (48,'Ideally Wolfram should produce the same prediction, but because its model [is continuously updating], the prediction may not be [the same].','理想情况下，Wolfram应该得出同一个预测值，但是因为程序的模型[不停在更新]，预测值可能不是[同一个值]。','en','zh','2025-10-07 18:05:53.000000',2,28),
 (49,'[To a human eye], the dog is still a Labrador albeit a bit [fuzzy]. Remember that this is not a [targeted] attack [in that] we [haven''t] trained the attack [using] the specific neural network used by the Wolfram site. If we did, we could develop something that would work at much lower levels of disturbance.','[人类的眼里]，狗纵使有点[糊]仍然是一只拉布拉多。记得这不是一个[针对性的]攻击，[这一点上]，我们[尚未]使用Wolfram网址已使用的具体神经网络，[就不能]训练攻击。我们训练了的话，我们就能够开发会以更低扰动水平工作的某个东西。','en','zh','2025-10-07 18:16:17.000000',2,29),
 (50,'Try the same attack but this time using another picture - one of a bear:','试试同一个攻击，但这次再使用一张图，其中一只熊的图就能攻击：','en','zh','2025-10-07 18:17:26.000000',2,30),
 (51,'You can right click on this and save it to your share folder and then run the program again. You might see [the confidence dropping], but the prediction should still be the same - a brown bear. Obviously, not all photos/pictures [are well equipped for] the perturbations applied using the provided [exploit code], but there are many other libraries available that perform better perturbations.','你可以右键点击这张图并把图保存到你的分享文件夹，然后再运行程序。你可能会见到[置信值在下降]，但预测值应该仍然是同一个值 - 一只熊。很显然，不是所有的照片/图片都使用提供的[挖洞代码]就能[预备好]已施加的扰动，但有很多其他完成更好的扰动用得到的库。','en','zh','2025-10-07 18:33:32.000000',2,31),
 (52,'Try with your own images - note that they need to be [the appropriate size of 700px wide] so [scale them down] by resizing in photo editing software if they are larger.','用你自己的图像试试 - 注意图得要是[合适的大小为700px宽]，所以图比较大的话，在照片编辑软件[调整大小]就能[缩小图的比例]。','en','zh','2025-10-07 18:36:27.000000',2,32),
 (53,'Detecting malware relies on a static analysis of features such as the hash of the file and its use of strings (as we saw when we used Yara to identify malware). This is fine if you encounter malware that is something you have in a database of malware samples. Machine learning however tries to identify new malware by analysing the features and using a model that has been trained on millions of previous samples to be able to answer the question of whether the program is malware or not, rather than identifying the specific type of malware.','检测恶意软件依赖对特征的静态分析，譬如（我们使用了Yara去认出恶意软件的时候我们所看到的）文件的哈希码和码对字符串的使用。你遇到是你在一个恶意软件样本数据库中有的某个东西的恶意软件的话，这就还好。机械学习不过就使用一下已经在数百万之前的样本上训练出来回答得出程序是恶意软件与否，而非识别具体类型的恶意软件的问题的一个模型，就能认出新的恶意软件。','en','zh','2025-10-07 20:16:48.000000',2,33),
 (54,'The Elastic Malware Benchmark for Empowering Researchers (Ember) (https://github.com/elastic/ember) is a neural network that uses features extracted from binary files to train a model that can distinguish malware from regular Windows'' programs.','授权研究人员弹性恶意软件基准（Ember）（https://github.com/elastic/ember) 是使用二进制里已提取的特征去训练可以在常规Windows程序里辨别恶意软件的一个模型的一个神经网络。','en','zh','2025-10-07 20:20:15.000000',2,34),
 (55,'To do this, Ember uses a framework called LIFE that will analyse Windows (and other platforms) [binaries] (https://github.com/lief-project/LIEF). The data that LIFE produces [then] uses a fingerprint of the binary [and] can be used to train the model. Let''s start the docker container to run Ember:','要做到这一点，Ember使用将分析Windows（和其他平台）[二进制]（https://github.com/lief-project/LIEF） 的一个叫做LIFE的框架。LIFE产出的数据[然后就]使用二进制的一个“指纹”[就]可以使用来训练模型。我们来开启docker匣子去运行Ember：','en','zh','2025-10-07 20:30:32.000000',2,35),
 (56,'To test the model cd on the same docker container to the directory /opt/ember. The model has been pre-trained and so you don''t need to do that, although if you are interested, you can (look at the GitHub page).','要测试模型，在同一个docker匣子上cd到目录/opt/ember。模型已经预训练，并且你不用那么做，尽管你有兴趣的话你就可以（看GitHub页面）去预训练。','en','zh','2025-10-07 22:45:20.000000',2,36),
 (57,'First, unzip the malware (with the usual password: infected):','首先，（用通常的密码：infected）拉开恶意软件。','en','zh','2025-10-07 22:46:09.000000',2,37),
 (58,'To test the malware, we can use the following command:','要测试恶意软件，我们可以使用如下指令：','en','zh','2025-10-07 22:46:31.000000',2,38),
 (59,'The script classify_binary.py takes the trained model as an argument and the binary file to analyse. As you can see, the sample malware is given a >99% [probability] [of being malware].','脚本classify_binary.py把训练模型取为变量和二进制文件去分析。可见，样本恶意软件给到了>99%的[概率][是恶意软件]。','en','zh','2025-10-07 22:52:11.000000',2,39),
 (60,'This *is* [real] malware - [do] not download to your PC [or try] and execute.','这是[真实存在的]恶意软件不要下载到你的PC[或者尽量不要]执行。','en','zh','2025-10-07 22:52:51.000000',2,40),
 (61,'The malware is actually Trickbot, which is a [banking trojan].We can now try with a normal Windows program git.exe.','恶意软件实际上是Trickbot，是一个[银行木马]。我们现在就可以试试用一个正常的Windows程序git.exe。','en','zh','2025-10-07 22:55:41.000000',2,41),
 (62,'What is returned is a *very* small number 1.7*10-7. In other words, a [practically] 0 score [for it being malware].','返回的是一个*非常*小的数字1.7*10-7。换句话说，[测出来是恶意软件][简直]0分','en','zh','2025-10-07 23:00:16.000000',2,42),
 (63,'Msfvenom is a utility that comes with what is called an exploitation framework called Metasploit. Metasploit is a [sophisticated] [toolset] that is used by penetration testers (and hackers) to explore vulnerabilities and exploit them. Msfvenom can generate various [payloads] that when run on a target machine, will create remote access to that machine for attackers. One of these payloads is called a Meterpreter shell and normally this is recognised as malware by anti-malware software.','Msfvenom是自带所谓叫做Metasploit的挖洞框架的一个协程。Metasploit是被渗透测试员（和黑客）是用来探究并利用漏洞的一个[高精密][工具套组]。Msfvenom可以生成在一个目标机械上运行时就可以给攻击者创造那个机械的远程访问权的各种[装载码]。这些装载物的其中一个叫做Meterpreter shell，而正常情况下这个shell被杀毒软件识别为恶意软件。','zh','en','2025-10-08 17:57:47.000000',2,43),
 (64,'Msfvenom comes with [a variety of] evasion techniques to avoid detection but most are easily detected by anti-malware software. However, there exists one approach that [does fool] anti-malware, especially machine learning classifiers.','Msfvenom自带[各种各样的]回避技巧去规避检测，但大多数都很容易被杀毒软件检测到。不过存在一个[糊弄到]恶意软件的措施，尤其是机械学习分类器。','en','zh','2025-10-08 17:58:47.000000',2,44),
 (65,'[To get started], we are going to run Metasploit. But firstly, we will create a [local volume] [that we can attach to different containers] - this is due to the files we are about to create will most likely [be filtered] automatically by your firewall. So let''s create a temporary volume. In your PowerShell/terminal:','[一开始的话]，我们要运行Metasploit。但首先，我们将创建[我们可以附在不同匣子上的]一个[本地卷] - 这主要是我们即将创建的文件有可能将你的防火墙被自动[筛掉]。所以我们来创建一个暂时的卷。在你的PowerShell/terminal中：','en','zh','2025-10-08 17:58:58.000000',2,45),
 (66,'This will create a local volume named volume1, you can check by docker volume ls. Now we can attach this volume instead of host''s [local drive] and share files between containers. Let''s run a Docker container as follows:','这将创建一个名为volume1的本地卷，你可以拿docker volume ls来检查。好了我们可以附加这个卷，而不是主机的[本地驱动器]，并在匣子之间分享文件。我们来运行如下的Docker匣子：','en','zh','2025-10-08 20:42:36.000000',2,46),
 (67,'This will create a folder called volume1 in the root directory (you can name this [something else] e.g., volume1:/extra), which is attached to the local volume1.','这将在root目录（你可以把这个目录叫做[别的什么]，如volume:/extra）创建一个叫做volume1的文件夹。','en','zh','2025-10-08 20:42:46.000000',2,47),
 (68,'Then, we [are going to need] a file called putty.exe that we are going to use as a template for one of the Meterpreter versions. If you have a [shared] folder between the container and the host, download it by going to the address below and save it to the directory you have shared with the container (you can paste the link in the browser to download, and save it into the shared folder:)','然后，我们[得打算要]一个叫做putty.exe的文件
我们打算使用为其中一个Meterpreter版本的一个模板。你在匣子和主机之间有一个[共同的]文件夹的话，就转到以下的地址就可以下载并把文件保存到你与匣子已经共享的目录（你可以粘贴浏览器中的链接去下载并把文件保存进共用的文件夹中：）','en','zh','2025-10-08 20:57:03.000000',2,48),
 (69,'Alternatively (e.g., using the shared local volume approach), you can use wget to download directly from docker (and move it into the shared folder). You would need to apt-get update and apt-get install wget on the container.Now, we can run Metasploit by typing: msfconsole. If you are asked questions, answer yes to the first question (set up a new database) and no to the second ([init] the web service). After doing that, you should see [something like this] (the actual graphic [changes] each time):','要不然（可以使用共用的本地卷措施）你就能在docker里面使用wget直接下载（把文件移动进共用的文件夹）你得要会在匣子上apt-get update和apt-get install wget。好了我们运行Metasploit，msfconsole就可以了。你被问问题的话，第一个问题回答是（设置一个新的数据库）第二个回答否（[初始]web服务）。答那个问题之后，你应该看到[这样的]（实际的图形每次都[在变]）：','en','zh','2025-10-08 22:38:02.000000',2,49),
 (70,'[The graphic changes each time you load it] so don''t worry if your version doesn’t show [Missile] Command - [and in case] you [were wondering] - Missile Command was a very popular video game back [in the 1980''s] :)','[你每次加载图形，图形都在变化]，所以你的版本上没有[投射物]命令（Missile Command）- [而以防万一]你[真想知道] - 《导弹指挥官》（同名）[早在20世纪80年代]是一个玩的人非常多的游戏 :)','en','zh','2025-10-08 22:55:10.000000',2,50),
 (71,'We are going to run msfvenom from the Metasploit command line to generate two versions of meterpreter [executables]. The first will run an unmodified meterpreter executable:','我们打算在Metasploit命令行里运行msfvenom去生成两个版本的meterpreter[执行档]。第一个将运行一个未修改的meterpreter执行档：','en','zh','2025-10-08 22:55:24.000000',2,51),
 (72,'You don''t really have to worry about the parameters but if you are interested, the LHOST and LPORT arguments tell Meterpreter where to connect back to (i.e. our machine). We haven''t set up a [listener] on port 4443 and our executable actually doesn''t send back anything, so these values are just there [as a space holder]. The -f exe tells Meterpreter that we are using an executable format for the payload.','你不必真的担心变量，但你有兴趣的话，LHOST和LPORT变数就给Meterpreter说要连接回到的地方（换言之我们的机械）。我们并没有在端口4443上设置[侦听器]，而我们的执行档实际什么都没有发送回来，那么这些值只是在那[当一个空格位符]。-f exe给Meterpreter说，我们在给装载物使用一个可执行的格式。','en','zh','2025-10-09 08:34:08.000000',2,52),
 (73,'Now we will create a second version that will effectively embed Meterpreter in a normal Windows executable putty.exe. Putty is an application that allows SSH connections on a Windows box. I have saved putty.exe in the /volume1 (shared) directory. Run the msfvenom command as follows:','好了我们将创建将有效地把Meterpreter嵌入到一个正常的Windows执行档putty.exe中的第二个版本。Putty是一个允许在Windows盒子里SSH连接的应用。我已经把putty.exe保存到/volume1（共用的）目录了。运行如下的msfvenom指令：','en','zh','2025-10-09 08:54:27.000000',2,53),
 (74,'[Moreover], Msfvenom has other encoders that try and [obfuscate] the file to avoid detection. One of these is called shikata ga nai. You can create a meterpreter binary using the flag:','[此外]，Msfvenom有尽量[混淆]文件去规避探测的
其他编码器。这些编码器其中一个叫做shikata ga nai。你可以使用旗子，就能创建一个meterpreter二进制：','en','zh','2025-10-09 08:54:51.000000',2,54),
 (75,'Now that we have the three different samples, we can go back to our [classifier] in the ai-malware container and see what happens. [Launch] the ai-malware container with the volume1 attached (it will be a new container instance of the ai-malware image):','现在我们有三个不同的样本，我们在我们的ai-malware匣子中可以转回到我们的[分类器]并看情况。[启动]已附加voulme1的ai-malware匣子
（将是ai-malware图像的一个新匣子实例）。','en','zh','2025-10-09 09:06:21.000000',2,55),
 (76,'Now, move the meterpreter files into the /opt/ember directory. With the first version meterpreter1.exe we get:','好了，把meterpreter文件移动进/opt/ember目录。使用第一个版本meterpreter1.exe，我们得到：','en','zh','2025-10-09 09:18:44.000000',2,56),
 (77,'[Definitely malware]! However, when we run the second version, we get:','[绝对是恶意软件]！不过我们运行第二个版本的时候，我们就得到：','en','zh','2025-10-09 09:26:01.000000',2,57),
 (78,'So, according to the classifier, this is likely to be a normal, and safe, binary/executable! And [for] the last one:','所以根据分类器所述，这有可能是一个正常且安全的二进制/执行档！而[测]最后一个：','en','zh','2025-10-09 09:29:20.000000',2,58),
 (79,'It is important to note that [machine learning evasion by masquerading as a normal binary] is not an adversarial technique. [You have simply overwhelmed the classifier with enough features of normal binaries] that it tips it into classifying it [as such]. Adversarial techniques in malware are more difficult than with images because you are more limited in [what you can change]. You still [want] a binary that works after your changes [and so] randomly changing bits of the file can easily [stop it from doing that].','注意到[机械学习伪装成一个普通二进制就可以回避]不是一个对抗技巧很重要。[你只不过是给分类器灌输足够多的普通二进制功能而已]，分类器才倒向把二进制[如此]分类。恶意软件中的对抗技术比用图像的难，是因为你比较受限于[你可以改的内容]。在你改动后你仍然[需要]一个能用的二进制，[因此]随机地改变文件的数位可以很容易[让他不那么做]。','en','zh','2025-10-09 10:28:20.000000',2,59),
 (80,'Don''t forget to delete all malware samples and also delete the local volume you created that contains the meterpreter files.','别忘记删除所有恶意样本并且删除你创建的、装meterpreter文件的本地卷。','en','zh','2025-10-09 10:29:51.000000',2,60),
 (81,'If you are interested, upload the meterpreter versions you created to VirusTotal and see [what they are classified as there].','你有兴趣的话，把你创建了的meterpreter版本上传到VirusTool并看版本[在那分类成什么]。','en','zh','2025-10-09 10:31:24.000000',2,61),
 (82,'It uses [single-pixel image] that steals your sensitive chat data and sends it to a malicious third-party. Full PDF-version','攻击使用窃取你敏感聊天数据的[单像素图像]并把图像发送给一个恶意第三方。完整PDF版本。','en','zh','2025-10-09 13:18:22.000000',2,62),
 (83,'I[''ve discovered] new prompt injection attack [aimed at] the users of ChatGPT web version. The attack [lets] perform a prompt injection on ChatGPT chat, modifying chatbot answer with an invisible single-pixel markdown image that [exfiltrates] the user''s sensitive chat data to a malicious third-party. It can be [optionally] extended to affect all future answers, making injection persistent. It doesn''t take advantage of any vulnerabilities, but rather combines a set of tricks creating an effective way [for a user trickery].','我[才发现]新的[以]ChatGPT web版用户[为目标]的提示词插入攻击。该攻击用一张把用户的敏感聊天数据[漏出到]恶意第三方的不可见单像素markdown图像，[来]改动聊天机械人的回答，在ChatGPT聊天上就能完成一次提示词插入。攻击可以使得插入[持久]，就能[有选择地]扩展到影响所有以后的答案。攻击没有利用任何的漏洞，而是创建一个[欺骗一次用户]的有效方法，就能组合一组技巧。','en','zh','2025-10-09 14:13:49.000000',2,63),
 (84,'Dictionaries are collections of [unordered] and distinct key/value pairs, where key values are unique, but value can be repeated. The type name for dictionaries are ''dict''.','字典是一套[未排序]且独有的钥匙/值对，其中钥匙值唯一，但值可以重复。字典名称类型是''dict''。','en','zh','2025-10-09 15:41:30.000000',1,1),
 (85,'As in the previous section, type the line or lines given the left column into your Python shell, inspect the output, read the notes, and figure out what’s happening!','如之前的一节，把行或者左列已给到的行打进你的Python shell、审查输出、阅读笔记并弄清什么情况！','en','zh','2025-10-09 15:53:15.000000',1,2),
 (86,'bird_count = {''kiwi'' : 3, ''weka'' : 1, ''kereru: 7''}
bird_count = [''kiwi'' : 3] #returns 3
bird_count = [''piegon''] #key error!
You can create a dictionary containing key/value pair items using [the curly brackets]. You can check the value assigned with a key by accessing the dictionary [indexed] with the key value. When accessing using a key, make sure the key exists otherwise it will give you an error.','bird_count = {''kiwi'' : 3, ''weka'' : 1, ''kereru: 7''}
bird_count = [''kiwi'' : 3] #returns 3
bird_count = [''piegon''] #key error!
你可以使用[花括号]就能创建一个字典包含键/值对的项。你可以访问用键值[索引的]字典，就可以检查已用键赋的值。使用一个键就能访问时，就确保键存在，否则程序会给你错误。','en','zh','2025-10-09 17:07:28.000000',1,3),
 (87,'empty_dict = dict()
empty_dict = {}
You can create an empty dictionary using the dictionary constructor, as well as using the empty curly brackets.','empty_dict = dict()
empty_dict = {}
你可以使用字典构造器以及使用空的花括号就能创建一个空的字典。','en','zh','2025-10-09 17:14:24.000000',1,4),
 (88,'''kiwi'' in bird_count
''pigeon'' in bird_count
To avoid getting an error, you can check if the key exists in the dictionary or [not using the in operator].','''kiwi'' in bird_count
''pigeon'' in bird_count
要规避得到一个错误，你可以检查键在字典里是否存在，或者[不使用in运算符就能]。','en','zh','2025-10-09 17:14:43.000000',1,5),
 (89,'bird_count[''pigeon''] = 10
To create a new entry in the dictionary, just specify the key and assign the value.','bird_count[''pigeon''] = 10
要在字典里创建一个新的条目，具体说明键并把赋给值就行了。','en','zh','2025-10-09 17:15:00.000000',1,6),
 (90,'del bird_count[''pigeon''] = 10
bird_counts.pop(''kiwi'')
You can use either the del command or the pop method to remove a key/value pair item from the dictionary.','del bird_count[''pigeon''] = 10
bird_counts.pop(''kiwi'')
你要么可以使用del命令，要么使用pop方法在字典里去移除一个键/值对的项。','en','zh','2025-10-09 17:32:39.000000',1,7),
 (91,'my_dict.clear()
clear method removes all items in the dictionary. Be careful while using it.','my_dict.clear()
clear方法在字典中移除所有的项。使用的时候要小心。','en','zh','2025-10-09 17:33:02.000000',1,8),
 (92,'bird_counts.keys()
key method returns dictionary iterable that contains keys only.','bird_counts.keys()
key方法返回仅包含键的字典迭代项。','en','zh','2025-10-09 17:33:22.000000',1,9),
 (93,'bird_counts.items()
items method returns the dictionary iterable item that contains the key/value pairs. This can be used in the for-loop to [go over] both key and value pairs.','bird_counts.items()
items方法返回包含键/值对的字典可迭代项。这可以在for-loop中使用来[跑通]键和值两者的对。','en','zh','2025-10-09 17:33:42.000000',1,10),
 (94,'bird_counts.values()
values method returns dictionary iterable that contains values only.','bird_counts.values()
values方法返回仅包含值的字典迭代。','en','zh','2025-10-09 17:33:57.000000',1,11),
 (95,'Accessing a dictionary. Write a function get_name(name_dict, id_num) that takes as its first parameter a dictionary mapping an ID number to a name and as its second parameter a particular ID number (which might be [invalid]) and returns the name associated with the given ID number if [that] ID number exists in the dictionary or None [otherwise].','评估一个字典。写取一个ID映射到一个名字上的字典取作其第一个变量，取一个特定的ID编号（可能会[无效]）取作其第二个变量，[给出的ID号码]存在并返回与[那个]ID编号相关联的名称，[否则的话]返回None的一个方程get_name(name_dict, id_num)。','en','zh','2025-10-09 17:45:16.000000',1,12),
 (96,'[Counting words] in a string. Write a function word_counter(input_str) which takes a string input_str and returns a dictionary mapping words in input_str to their occurrence counts. You may assume for this question that the list of words in input_str [is just] input_str.split() except that words must be converted to lower case [at some point]. Note that [the order in which] (key, value) pairs are displayed when printing a dictionary is arbitrary -- you cannot control that, it doesn''t affect the correctness of your answer. To get a consistent print out we extract the items from the dictionary and sort them. :)','在一个字符串里[数字数]。编写一个方程word_counter(input_str)，取一个字符串input_str并返回把input_str的字词映射到他们出现的数上的一个字典。你这个问题不妨假设在input_str中的词的list，除开字词[有的时候]必须转化为小写[就是]input_str.split()。注意一下，打印一个字典任意时(key, value)对里[从中]显示出来[的顺序]——你无法控制[那顺序]，它没有影响你答案的正确性。要获得一个连续的[打印码]，我们在字典里提取项并给项排序。:)','en','zh','2025-10-09 18:13:11.000000',1,13),
 (97,'Finding a key, given a value. Write a function find_key(input_dict, value) that takes as a parameter a dictionary and a value and returns the key in the dictionary that maps to the given value or None if no such key exists. In other words, the function finds the key [such that] input_dict[key] == value. You may assume that [there is at most one such key] in dictionary.','鉴于值，求出键。写取一个字典取作参数，并返回在投射到给出的值或者没有这样的键存在返回None的字典中的键的一个方程find_key(input_dict)。换句话说，函数求出键，[如此以来]input_dict[key][才]==value。你不妨假设，在字典中[顶多有一个这样的键]。','en','zh','2025-10-09 20:16:52.000000',1,14),
 (98,'Inverting a dictionary. Write a function make_index(words_on_page) that takes a dictionary [mapping from] page number [to] a list of the unique words on that page and returns a dictionary that maps from a word to an ordered list of pages [on which] that word appears. All words are [lower case].','翻转字典。写取在页面上[从]那个页面编号[投射到的是]一个列表唯一单词上的一个字典，并返回从一个单词投射到一个有序列表的页面上的一个字典，那个单词[在此之上]出现的一个函数make_index(words_on_page)。所有单词都是[小写]。','en','zh','2025-10-09 21:03:43.000000',1,15),
 (99,'For example, if a [3 page book] contains [just] the sentences hi there fred on [page 1], the sentence there we go go go on page 2 and fred was there was there on page 3, the input dictionary words_on_page would be {1: [''hi'', ''there'', ''fred''], 2: [''there'', ''we'', ''go''], 3: [''fred'', ''was'', ''there'']}','比如，一本[3页的书][就]包含在[第一页]上的句子hi there fred、在第二页上的句子there we go go go和在第三页上的句子fred was there was there[而已]的话，输进词典words_on_page会是{1: [''hi'', ''there'', ''fred''], 2: [''there'', ''we'', ''go''], 3: [''fred'', ''was'', ''there'']}','en','zh','2025-10-09 21:04:05.000000',1,16),
 (100,'The function should then return the dictionary {''hi'':[1], ''fred'':[1, 3], ''there'': [1, 2, 3], ''we'' :[2], ''go'': [2], ''was'': [3]} [showing] that ''hi'' appears only on page 1, ''fred'' appears on pages 2 and 3, etc.','函数然后应该返回[上面有着]''hi''只在第一页出现、''fred''只在第二页和第三页等出现的字典{''hi'':[1], ''fred'':[1, 3], ''there'': [1, 2, 3], ''we'' :[2], ''go'': [2], ''was'': [3]}。','en','zh','2025-10-09 21:04:34.000000',1,17),
 (101,'Remember that the order of keys in a dictionary is arbitrary. Warning: this question [is a significant step up] [in complexity] [from other questions in this quiz].','记住在一个字典中的键的顺序任意。警告：这个问题[在这个小测中其他问题里][复杂性上][上很大一个台阶]。','en','zh','2025-10-09 21:04:52.000000',1,18),
 (102,'Counting words in a file #1. A psychology student [is carrying out] an experiment in which she repeatedly asks people to think of an object, [any] object. She wants to see what objects people think of under this situation. She enters each guessed object into a text file, [one object per line]. Help her to analyse the data by writing make_dictionary(filename) that reads the named files and returns a dictionary mapping from object named to [occurrence counts] ([the number of times] the particular object was guessed). For example, given a file mydata.txt containing the following','数一个文件中的词数#1。一名心理学学生[在进行]一项实验，她在此之中重复问人们think of an object, any object（“思考一个对象，[什么]对象[都可以]”）她需要明白在这种情形下人们思考什么物体。她把每个猜测的对象输入进一个文本文件，[每行一个对象]。编写读取命名的文件并返回从已命名的对象投射到的是[出现数]（特定对象猜测了的[次数数字]）的make_dictionary(filename)就可以帮助她分析数据。比如已给一个包含的是如下内容的一个文件mydata.txt。','en','zh','2025-10-10 09:02:02.000000',1,19),
 (103,'The function would return a [dictionary-like] {''dog'': 2, ''persian cat'': 3, ''triceratops'': 1, ''large white fluffy thing'': 1}. The order of keys in a dictionary is arbitrary, so the objects might be in any order when the dictionary is printed.','函数会返回一个[字典一样的]{''dog'': 2, ''persian cat'': 3, ''triceratops'': 1, ''large white fluffy thing'': 1}。一个字典中的键的顺序任意，所以字典打印时，对象可能会按照任何顺序。','en','zh','2025-10-10 09:04:32.000000',1,20),
 (104,'[Notes]:
·This program requires [only] about 8 - 12 lines of code. If you[''re finding] you [need more than that], ask a tutor for help.
·[Leading] and [trailing] white space should be [stripped] from object names.
·Empty object names (e.g. blank lines or lines with only whitespace) should be ignored.
·Some test files can be downloaded here, unzip them into your program folder.','[备注]：
·这个程序[只]需约8-12行代码[而已]。你[正发现]你[还得要比那多]的话。
·[前面]和[后面的]空格应该在对象名称里[去除]。
·空的对象名称（如空行或只有空格而已）应该无视。
·一些测试文件可以在这下载，把他们拉开进你的程序文件夹中。','en','zh','2025-10-10 09:25:17.000000',1,21),
 (105,'Making a dictionary from a CSV file. Every edition of each book published by a particular publisher has a unique ISBN - International Standard Book Number -- printed in the publication information [at the start of the book]. You may assume that there are no commas within book titles or author names, so that each file line can be split with line.split('','') to yield an [author, title, isbn] list. You can treat ISBNs as strings.','做一个CSV文件里的一本字典。一个特定的出版商已出版的每本书的每一个版本都有[在书的开头]已打印在出版信息中唯一的ISBN—International Standard Book Number（“国际标准图书编号”）。你不妨假设书本标题或作者名称之内没有逗号，这样每个文件行才可以用line.split('','')分隔，来得一个[author, title, isbn]list。你可以把ISBN当成字符串。','en','zh','2025-10-10 09:55:29.000000',1,22),
 (106,'loop makes a [sorted] list of the keys in the dictionary and then uses this to [iterate through] the dictionary. Compare print(list(sorted(your_dict.keys())) to print(your_dict.keys()) to see [what is going on]. Please [ask us for further explanation] [if you are still not sure what is going on]... If the input file doesn''t exit then your program must [catch the exception] and print the error message The file {filename} was not found. (where {filename} is the filename provided, see example below) and return None. This should be caught with FileNotFoundError exception handler.','loop在字典中做一张[排好的]列表，然后使用这张表[把]字典[迭代通]。把print(list(sorted(your_dict.keys()))和print(your_dict.keys())比较去明白[是怎么一回事]。[你仍然不清楚是怎么一回事的话]，请[另找我们问解释]...输进文件没有退出的话，那么你的程序就必须[接住例外情况]并打印错误信息The file {filename} was not found.（其中{filename}是已提供的文件名，见以下的示例）并返回None。这应该用FileNotFoundError例外情况处理器来接住。','en','zh','2025-10-10 10:42:55.000000',1,23),
 (107,'Note: 1. This program requires only about 8 -12 lines of code. If you''re finding you need more than that, [ask a tutor for help]. 2. [Be careful to strip the newline character off the end of each line]. 3. We don''t provide you with any test data files [for this question] - being able to create your own test data is a [vital] skill in programming. You should create your own test data file, e.g. by coping the example data above, pasting it into a new file window in Wing and saving it as books.csv.','备注：1. 这个程序只需约8-12行代码。你正发现你还得要    比那多的话，[找一个导师求助]。2. [小心从你每行的末尾去掉新行符]。3. 我们没提供给你[这道题]任何测试数据文件 - 创建得出自己的测试数据在编程中是一个[至关重要的]技能。你比如就应该拷贝以上的示例数据、在Wing中把数据粘贴进一个心的文件窗口并把文件保存为books.csv就可以创建你自己的测试数据文件了。','en','zh','2025-10-10 10:54:30.000000',1,24),
 (108,'For example, if the input file were:
Kurt Vonnegut,Breakfast of Champions,0-586-08997-7
Lloyd Jones,Mister Pip,978-0-14-302089-9
Joe Bennett,So Help me Dog,1-877270-02-4
Orson Scott Card,Speaker for the Dead,0-812-55075-7','比如，输进文件是
Kurt Vonnegut,Breakfast of Champions,0-586-08997-7
Lloyd Jones,Mister Pip,978-0-14-302089-9
Joe Bennett,So Help me Dog,1-877270-02-4
Orson Scott Card,Speaker for the Dead,0-812-55075-7
的话','en','zh','2025-10-10 10:55:46.000000',1,25),
 (109,'the output dictionary would be (in some arbitrary order)
{''0-586-08997-7'': (''Kurt Vonnegut'', ''Breakfast of Champions''),
''978-0-14-302089-9'': (''Lloyd Jones'', ''Mister Pip''),
''1-877270-02-4'': (''Joe Bennett'', ''So Help me Dog''),
''0-812-55075-7'': (''Orson Scott Card'', ''Speaker for the Dead'')}','输出字典（按某种任意顺序）就会是{''0-586-08997-7'': (''Kurt Vonnegut'', ''Breakfast of Champions''),
''978-0-14-302089-9'': (''Lloyd Jones'', ''Mister Pip''),
''1-877270-02-4'': (''Joe Bennett'', ''So Help me Dog''),
''0-812-55075-7'': (''Orson Scott Card'', ''Speaker for the Dead'')}','en','zh','2025-10-10 10:56:01.000000',1,26),
 (110,'Write a function long_enough(string, min_length) that returns a list of all the strings in the list strings with [a length greater than or equal to] the given min_length.','编写用[一个长度大于或等于]给出的min_length在list strings中返回一个列表的全部字符串的一个函数long_enough(string, min_length)。','en','zh','2025-10-10 11:15:32.000000',1,27),
 (111,'Define a function my_enumerate(items) that [behaves in a similar way to] the built-in enumerate function. It should return a list of tuples (i, item) where item is the ith item, with 0 origin, of the list items (see the example below). [Check the test cases for how the function should work]. Your function must not call python''s inbuilt enumerate function.','定义[运作起来与]内置的enumerate函数[类似]的一个函数my_enumerate(items)。函数应该返回一个列表的tuple (i, item)，其中项是第i个项，0原点，为list的项（见以下的示例）。[检查测试案例函数应该怎么用]。你的函数必须没有调用python的置于内部的enumerate函数。','en','zh','2025-10-10 11:26:29.000000',1,28),
 (112,'Sequences of numbers in which there are frequent runs of a particular number repeating several times can often be more [compactly] represented by use of what is called [run length encoding]. A list is run-length encoded by representing it as a list of pairs (2-tuples), where each pair is a number and the length of the run of that number, where the length is 1 if a number occurs once, 2 if it occurs twice in a row, etc. Write a function run_length_encode(nums) that returns the run-length encoded representation of the list of integers, nums.','有一个特定数字重复多次频繁跑的数字序列，对所谓[游程编码]进行使用就可以比较[紧凑地]表示。一个list把自身表示为一个list的对（2-tuples）就可以游程编码，其中每个对是一个数字和那个数字跑的长度，其中数字发生一次的话长度是1，数字连着发生两次的话长度是2等。编写返回对list的整数nums进行游程编码表示的一个函数run_length_encode(nums)。','en','zh','2025-10-10 13:48:07.000000',1,29),
 (113,'Write your own function series(x) which takes a single argument x and returns the sum of [the series]. The calculation should [be approximated to] [the first few terms] till the term becomes similar than x. Round your final answer to 4 decimal places [of accuracy] before returning it.','编写你自己的函数series(x)，取单个变量x并返回[级数]的和。计算应该[近似于][前几项]，直到项与x相似。把你最后的答案整入，[精确到]4位小数，再返回。','en','zh','2025-10-10 15:56:31.000000',1,30),
 (114,'Note: You have to be careful with the last calculated term. Depending on the formulation of your loop, you may need to add or remove it from the total sum to match your result. This will help you to understand the loop [in better manner].','备注：你得小心最后一个计算的项。看你的循环公式，你可能得要在总和里添加或者移除最后项去匹配你的结果。这将帮助你[多多少少更好]去理解循环。','en','zh','2025-10-10 15:56:42.000000',1,31),
 (115,'Let''s say that we have a contest [the details of which] we don''t care about [apart from] one simple rule. If a [contestant] earns a score equal to or greater than the k-th place [finisher], they will [advance to] the next round if their own score is greater than 0. So write a function nextRound(k, scores) which will count how many contestants will [progress to] the next round. There will be no more than 20 contestants, and 1 <= k <=20. The scores will be given in an order, but contestants can have the same score.','比方说，我们有一个竞赛，我们[除了]其中一条简单的规则[外]，没在意[其中的细节]。“一名[参赛者]获得等于或大于第k名[比完的人]的一个分数的话，他们的分数大于0的话就将[晋级到]下一轮。”所以编写一个函数nextRound(k, scores)，将数多少名参赛者将[接着到]下一轮。将有不超过20名参赛者，而1 <= k <=20。分数将按照一个顺序给出，但参赛者都有同一个分数。','en','zh','2025-10-10 16:15:55.000000',1,32),
 (116,'Write a function singleDigit(N) to take a positive integer N as an input and add the digits of the input repeatedly until the result has a single digit.','编写一个方程singleDigit(N)去把一个正整数N取作一个输进并重复添加输进的位数，直到结果有单个位数。','en','zh','2025-10-10 16:28:14.000000',1,33),
 (117,'Write a function sequence(n) which takes any positive integer n, if n is even, divide it by 2 to get n/2. If n is odd, multiply it by 3 and add 1 to obtain 3n + 1. Store the results in a list and repeat the process until it [reaches] 1. At the end return the list and ensure that returned list only contain integer values.','编写一个函数sequence(n)，取任何正整数n，n是偶数的话，除以2得到n/2。n是基数，乘以3加1获得3n + 1。储存在一个list中的结果并重复进程，直到[到]1。最后的地方返回list并保证返回的list只包含整数值。','en','zh','2025-10-10 19:47:08.000000',1,34),
 (118,'Write a class car with attributes model, rego, year and color. Also create methods in the class to set and get each attribute such as setModel(modelName) and getModel() to set and obtain the model of the car’s object. Similarly write set and get methods for all the attributes of the class.','编写一个类car与属性model、rego、year和color。并且在class中创建方法去set（设置）和get（得到）属性，譬如setModel(modelName)和getModel()去设置并获得车的对象的型号。以此类推，给class所有属性编写set和get方法。','en','zh','2025-10-10 20:08:53.000000',1,35),
 (119,'Write a class player with attributes name, age and sport. Create methods in the class to set and get each attribute such as SetName(name) and getName() to set and obtain the name of the player''s object. Similarly write set and get methods for all the attributes of the class. However, this class is restricted to single sport, so make sport variable static.','编写一个class player与属性name、age和sport。创建在class中的方法去set并get每个属性，譬如SetName(name)和getName()去设置和获取玩家的对象名称。以此类推，给class的所有属性编写set和get方法。不过，这个class限制在单个运动，所以将sport变量设为静态。','en','zh','2025-10-10 20:46:28.000000',1,36),
 (120,'1. Lab Overview. The XYZ research institute collected information of different organisations from all over the world for their future investment purposes. The collected dataset contains several parameters about each organisation, such as name and id of the organisation, country of the organisation registration, category of work, foundation year, number of employees, median salary, [profit in 2020 and profit in 2021].','XYZ研究机构因未来的投资用途在全世界各地里收集了不同组织的信息。收集的数据组包含每个组织方面的几个变量，譬如组织的名称和id、组织登记的国家、工作分类、成立年份、雇员数、工资中位数、[2020年的利润和2021年的利润]。','en','zh','2025-10-13 16:57:34.000000',5,1),
 (121,'You are required to write a Python 3 program that will read a CSV file. After reading the file, your program is required to complete the following statistical tasks:','要你去编写会读取一个CSV文件的一个Python 3程序。阅读文档之后要你的程序去做完下列的数据任务：','en','zh','2025-10-13 16:57:34.000000',5,2),
 (122,'1) Create a dictionary and store the following information in it: a. [t-test] score of profits in 2020 and 2021 for each country. b. Minkowski distance between the number of employees and the median salary for each country.','1) 创建一本字典并在字典中储存如下的信息：a. 每个国家2020年和2021年利润的[t检验分数]。b. 每个国家雇员数和工资中位数之间的闵可夫斯基距离。','en','zh','2025-10-13 16:57:34.000000',5,3),
 (123,'2) Create a nested dictionary that contains the following information for each category of organisations. a. organisation ID’s, and a list of the following data [corresponding to] each organization ID: i. Number of employees. ii. Percentage of [profit change] from 2020 to 2021 (absolute value). iii. [Rank of the organisation within each category], [with respect to the number of employees].','2) 创建一本包含机构每个类别如下信息的嵌套的字典。a. 机构ID的，以及一列[对应的是]每个组织ID的如下数据的list：i. 雇员数。ii. 2020年至2021年[利润变化]的百分比（绝对值）。iii. [组织在每个类别内]、[就雇员数的排名]。','en','zh','2025-10-13 16:57:34.000000',5,4),
 (124,'2. Requirements. 1) You [are not allowed to] [import] any external or internal module in Python.','2. 要求. 1) [没有][允许]你在Python中[传入]任何外部或内部模组。','en','zh','2025-10-13 17:37:03.000000',5,5),
 (125,'2) Ensure your program does NOT call the input() function at any time. Calling the input() function will cause your program [to hang], [waiting for] input that the automated testing system will not provide (in fact, what will happen is that if the marking program detects the call(s), it [will not] test your code [at all] [which may result in zero grade]).','2) 保证你的程序没有随时调用input()函数。调用input()函数将等待自动测试系统将不会提供的输进（其实将出现的情况是打分程序探测调用的话，程序[将一点都不会]测试你的代码）[结果可能导致零分的成绩]，就能造成你的程序[挂起]。','en','zh','2025-10-13 17:37:03.000000',5,6),
 (126,'3) Your program should also not call print() function at any time except for the case of graceful termination (if needed). If your program has encountered an error state and [is exiting gracefully] then your program needs to return empty lists for OP1 and OP2, and -2 for OP3. [At no point should you] print the program’s outputs or provide a printout of the program’s progress in calculating such outputs. Outputs [should be returned by the program] [instead].','3) 你的程序也不应该随时调用print()函数，除非是优雅终止的情况（需要的话）。你的程序已经碰上一条错误状态并且[在优雅退出]了的话，然后你的程序得要返回OP1和OP2空的list、OP3返回-2。[你哪一会儿都不应该]打出程序的输出或者在计算这类输出的过程中提供程序进程的打印输出。输出[反而][应该程序来返回]。','en','zh','2025-10-13 17:37:03.000000',5,7),
 (127,'4) Do not assume that the input file names will [end in] .csv. File name suffixes such as .csv and .txt [are not mandatory in systems other than Microsoft Windows]. [Do not enforce within your program that] the file must end with a .csv or any other extension (or try to add an extension onto the provided csv file argument), [doing so can easily lead to loosing marks and syntax error].','4) 不要假设输进文件名[将是].csv[结尾]。文件名称后缀譬如.csv和.txt[在微软Windows以外的系统中没有强制]。[不要在你的程序内强制]文档必须以.csv或者其他任何扩展名结尾（或者在提供的csv文件变数上面添加一下扩展名）[这么做结果很容易就丢分且有容易语法错误]。','en','zh','2025-10-13 17:37:03.000000',5,8),
 (128,'3. Input. Your program must define the function main with the following syntax: def main(csvfile)','3. 输进','en','zh','2025-10-13 18:17:20.000000',5,9),
 (129,'The input arguments for this function are: ·csvfile: The name of the CSV file (as string) containing the record of the organisations around the world. The first row the CSV file will contain the headings of the columns. A sample CSV file “organisations” is provided with project sheet on LMS and Moodle.','你的程序必须用下列的语法定义函数main：def main(csvfile)','en','zh','2025-10-13 18:17:20.000000',5,10),
 (130,'4. Output. Two outputs [are expected]:
We expect 3 outputs in the order below.
i) OP1: A dictionary which will have country names as keys, and the corresponding value for each country (key) will be a list containing t-test score of profits in 2020 and 2021 and Minkowski distance between number of employees and median salary of the respective country. The expected output is in the following format:
{‘country1’: [t-test score, minkowski distance], 
‘country2’: [t-test score, minkowski distance],…, 
‘countryn’: [t-test score, minkowski distance]}','4. 输出。两个输出[期望有]：
我们按照以下顺序期望有3个输出：
i) OP1：一本字典，将有国家名称为键，而每个国家（键）对应的值将为包含的是2020年和2021年利润的t检验分数的一列list和雇员数和相应国家工资中位数之间的闵可夫斯基距离。期望的输出在如下的格式中：
{‘country1’: [t-test score, minkowski distance], 
‘country2’: [t-test score, minkowski distance],…, 
‘countryn’: [t-test score, minkowski distance]}','en','zh','2025-10-13 18:51:25.000000',5,11),
 (131,'4. Output. Two outputs [are expected]:
We expect 3 outputs in the order below.
i) OP1: A dictionary which will have country names as keys, and the corresponding value for each country (key) will be a list containing t-test score of profits in 2020 and 2021 and Minkowski distance between number of employees and median salary of the respective country. The expected output is in the following format:
{‘country1’: [t-test score, minkowski distance], 
‘country2’: [t-test score, minkowski distance],…, 
‘countryn’: [t-test score, minkowski distance]}','4. 输出。两个输出[期望有]：
我们按照以下顺序期望有3个输出：
i) OP1：一本字典，将有国家名称为键，而每个国家（键）对应的值将为包含的是2020年和2021年利润的t检验分数的一列list和雇员数和相应国家工资中位数之间的闵可夫斯基距离。期望的输出在如下的格式中：
{‘country1’: [t-test score, minkowski distance], 
‘country2’: [t-test score, minkowski distance],…, 
‘countryn’: [t-test score, minkowski distance]}','en','zh','2025-10-13 18:51:25.000000',5,12),
 (132,'ii) OP2: A nested dictionary ‘D’ which will store the different categories of organizations (such as ‘transportation’、‘apparel’, etc.) as keys and each corresponding IDs as keys within each category of organisations and information related to the organisation IDs as values. Each value of ‘d’ will be a list containing the following data for each organisations:','ii) OP2：一本嵌套的字典’D’，将把组织的不同分类（譬如’transportation’、’apparel’、等等）储存为键、把每个对应的ID储存为在每个分类之内的键、把与组织ID有关的信息储存为值。每个值为’d’将为一列包含的是如下每个组织数据的list：','en','zh','2025-10-13 20:39:26.000000',5,13),
 (133,'a. number of employees, b. Absolute percentage of profit change from 2020 to 2021, and c. rank of an organisation within each category with respect to the number of employees (sort them in descending order, the organisation with the higher number of employees holds the higher rank, where the highest rank is ‘1’). If two organisations have the same number of employees, sort them (the [tied] organisations’ IDs only) in descending order of their profit change. Below is format: {‘category1’:{‘organisation ID1’: [number of employees, absolute percentage of profit change, rank ],  ‘organisation ID2’: [number of employees, absolute percentage of profit change, rank ]}...','a. 雇员数，b. 2020年到2021年利润变动的绝对百分比，和c. 在每个类别内就雇员数的一个组织的排名（按照降序排序、雇员数比较多的组织持有比较高的排名，其中排名最高为’1’）两个组织有同一个雇员数，按照其利润变动的降序排列（仅限[绑定]机构的ID）。如下为格式：{‘category1’:{‘organisation ID1’: [number of employees, absolute percentage of profit change, rank ],  ‘organisation ID2’: [number of employees, absolute percentage of profit change, rank ]}...','en','zh','2025-10-13 20:39:26.000000',5,14),
 (134,'Note: All floating-point results should be rounded [to 4 decimal places]. In some cases, Python may automatically remove trailing zeros, [even after] rounding (e.g., 2.5000 may be displayed as 2.5). This is expected behaviour, so you do not need to worry about the [missing] zeros.','备注：所有浮点结果应该化整[到小数点后4位]。在有些情况下，Python可能自动地移除后面的0，[甚至在]四舍五入[后也会]（如2.5000可能显示为2.5）这是预期的行为，所以你们不用担心[没]0。','en','zh','2025-10-13 21:50:21.000000',5,15),
 (135,'Download Organisations.csv file from Moodle. An example of how you can call your program from the Python shell (and examine the results it returns) are: >>> OP1, OP2 = main(''Organisations.csv'')','下载Moddle里Organisations.csv文件。你在Python shell里可以怎么调用你的程序（并检验程序返回的结果）的一个例子是：>>> OP1, OP2 = main(''Organisations.csv'')','en','zh','2025-10-13 22:58:00.000000',5,16),
 (138,'stringAAAA','stringAAA','zh','en','2025-10-18 11:52:12.368348',NULL,NULL);
INSERT INTO entry_sources (entry_id,source_id) VALUES (1,2),
 (3,4),
 (4,4),
 (5,4),
 (7,5),
 (8,5),
 (10,5),
 (11,5),
 (6,4),
 (12,5),
 (14,5),
 (15,5),
 (16,5),
 (17,5),
 (13,5),
 (18,5),
 (19,5),
 (21,8),
 (23,8),
 (25,8),
 (26,8),
 (27,8),
 (28,8),
 (29,8),
 (30,8),
 (31,8),
 (20,5),
 (9,5),
 (24,8),
 (22,8),
 (2,2),
 (32,8),
 (33,8),
 (34,8),
 (35,8),
 (36,8),
 (37,8),
 (38,8),
 (39,8),
 (40,8),
 (41,8),
 (42,8),
 (43,8),
 (44,8),
 (45,8),
 (46,8),
 (47,8),
 (48,8),
 (49,8),
 (51,8),
 (52,8),
 (53,8),
 (54,8),
 (55,8),
 (57,8),
 (58,8),
 (59,8),
 (60,8),
 (56,8),
 (61,8),
 (62,8),
 (50,8),
 (63,8),
 (64,8),
 (65,8),
 (66,8),
 (67,8),
 (68,8),
 (69,8),
 (70,8),
 (71,8),
 (72,8),
 (73,8),
 (74,8),
 (75,8),
 (76,8),
 (77,8),
 (78,8),
 (79,8),
 (80,8),
 (81,8),
 (83,8),
 (84,9),
 (85,9),
 (87,9),
 (88,9),
 (89,9),
 (86,9),
 (90,9),
 (91,9),
 (92,9),
 (94,9),
 (95,9),
 (96,9),
 (97,9),
 (98,9),
 (100,9),
 (101,9),
 (93,9),
 (102,9),
 (103,9),
 (99,9),
 (104,9),
 (106,9),
 (107,9),
 (108,9),
 (109,9),
 (105,9),
 (110,9),
 (111,9),
 (112,9),
 (113,9),
 (114,9),
 (115,9),
 (116,9),
 (117,9),
 (118,9),
 (119,9),
 (120,10),
 (121,10),
 (122,10),
 (123,10),
 (124,10),
 (125,10),
 (126,10),
 (127,10),
 (128,10),
 (129,10),
 (130,10),
 (131,10),
 (132,10),
 (133,10),
 (134,10),
 (135,10),
 (82,8),
 (138,11);
INSERT INTO sources (id,name,url) VALUES (1,'CITS1003_CyberSecurity_Forensics',NULL),
 (2,'CITS1003 CyberSecurity Forensics',NULL),
 (3,'PHL4100 The Singularity - A Philosophical Analysis',NULL),
 (4,'PHIL4100 Ethics and Critical Thinking - The Singularity - A Philosophical Analysis',NULL),
 (5,'CITS1402 Relational Database Management - Lab 6 - Dental Clinic',NULL),
 (6,'OALD7-E&C',NULL),
 (7,'MyBatch',NULL),
 (8,'CITS 1003 Cybersecurity - Lab 10 - AI',NULL),
 (9,'CITS 1401 Python - Lab 6 - Dictionaries and classes/objects',NULL),
 (10,'CITS 1401 Python - Lab 7 - Project 2 - XYZ Research Institute',NULL),
 (11,'string',NULL);
CREATE INDEX idx_entries_text ON entries (src_text, tgt_text);
CREATE INDEX ix_articles_created_at ON articles (created_at);
CREATE INDEX ix_entries_created_at ON entries (created_at);
