#!/usr/bin/env python3
"""
Update all 9 đỉnh JSON files with correct motif data from official documentation.
This script rewrites the JSON files with accurate Vietnamese names and descriptions.
"""

import json
import os
from pathlib import Path

# Complete motif data from official documentation
MOTIF_DATA = {
    "thuan-dinh": {
        "file": "10_Data_ThuanDinh.json",
        "urn_name_vi": "Thuần Đỉnh",
        "urn_name_en": "The Urn of Purity",
        "urn_description": "Thụy hiệu của vua Đồng Khánh",
        "motifs": [
            ("Thuần đỉnh", "Thụy hiệu của vua Đồng Khánh"),
            ("Đào", "Cây đào, loài cây vừa cho hoa đẹp vào mùa xuân, vừa cho quả ngon"),
            ("Súc sa mật", "Cây sa nhân, loài cây có hạt dùng làm gia vị, lá, hạt và quả dùng làm dược liệu trong y học cổ truyền"),
            ("Hướng nhu", "Cây hương nhu, một dược liệu quen thuộc của người Việt xưa"),
            ("Hoàng đậu", "Cây đậu nành, một loài cây ngũ cốc họ đậu"),
            ("Quỳ hoa", "Cây hoa hướng dương, được trồng để lấy hoa làm cảnh và lấy hạt làm thực phẩm, dược liệu"),
            ("Hoàng anh", "Chim vàng anh, một loài chim đẹp có bộ lông màu vàng rực rỡ"),
            ("Tản Viên sơn", "Núi Tản Viên hay núi Ba Vì, ngọn núi thiêng gắn với truyền thuyết Sơn Tinh - Thủy Tinh"),
            ("Vĩnh Định hà", "Sông Vĩnh Định, con sông đào vua Minh Mạng cho khởi công ở Quảng Trị năm 1824"),
            ("Phong", "Gió"),
            ("Thạch Hãn giang", "Sông Thạch Hãn, con sông có vai trò quan trọng về giao thông và thủy lợi ở Quảng Trị"),
            ("Cần Giờ hải khẩu", "Cửa biển Cần Giờ, cửa ngõ đường biển trọng yếu của thành Gia Định (Sài Gòn)"),
            ("Đăng sơn ngư", "Cá rô ta, loài cá sống nhiều ở ruộng đồng, có biệt tài vượt cạn"),
            ("Bạng", "Con ngao, một hải sản được khai thác ở hầu khắp các vùng ven biển của Việt Nam"),
            ("Bài đao", "Giá gác đao, vật dụng thể hiện tinh thần võ học của người Việt xưa"),
            ("Đỉnh", "Loại thuyền thon nhỏ, nhiều tay chèo, dùng để đua trong các lễ hội và trong chiến đấu"),
            ("Nam mộc", "Cây gỗ chò, loại gỗ có độ bền cao được người Việt ưa chuộng trong xây dựng"),
            ("Ly ngưu", "Con bò tót, loài bò hoang dã có hình thể lớn và sức khỏe địch được cả hổ báo"),
        ]
    },
    "nghi-dinh": {
        "file": "09_Data_NghiDinh.json",
        "urn_name_vi": "Nghị Đỉnh",
        "urn_name_en": "The Urn of Determination",
        "urn_description": "Thụy hiệu của vua Kiến Phúc",
        "motifs": [
            ("Nghị đỉnh", "Thụy hiệu của vua Kiến Phúc"),
            ("Mai", "Cây hoa mai, loài cây nằm trong bộ Tứ quý Tùng, Cúc, Trúc, Mai"),
            ("Đàn mộc", "Cây hoàng đàn, loài cây cho gỗ có mùi thơm đặc biệt quý hiếm"),
            ("Quế", "Cây quế, loài cây được trồng để khai thác vỏ và thân gỗ với nhiều công dụng"),
            ("Biển đậu", "Cây đậu ván, loài cây ngũ cốc họ đậu được trồng phổ biến ở Việt Nam"),
            ("Hải đường hoa", "Hoa hải đường, loài hoa tượng trưng cho phú quý"),
            ("Hồ da tử", "Con đuông dừa, loài côn trùng đặc sản của Nam Bộ"),
            ("Quảng Bình quan", "Cửa ải Quảng Bình, một cửa ải án ngữ đường thiên lý Bắc Nam"),
            ("Cửu An hà", "Sông Cửu An, một con sông có vai trò quan trọng với nông nghiệp ở Hải Dương, Hưng Yên"),
            ("Nam Đẩu", "Sao Nam Đẩu, một mảng sao gồm sáu ngôi nằm ở hướng Nam"),
            ("Bạch Đằng giang", "Sông Bạch Đằng, dòng sông gắn với những chiến thắng huyền thoại của người Việt"),
            ("Thuận An hải khẩu", "Cửa biển Thuận An, cửa biển có vai trò chiến lược đặc biệt quan trọng với kinh thành Huế"),
            ("Lục hoa ngư", "Cá lóc, loài cá nước ngọt kích cỡ trung bình, cho thịt ngon"),
            ("Giới", "Cây rau cải, loài rau được trồng phổ biến, dùng để chế biến nhiều món ăn"),
            ("Trường thương", "Giáo dài, một loại vũ khí cơ bản của quân đội nhà Nguyễn"),
            ("Hải đạo", "Loại thuyền chèo rất linh hoạt phục vụ hoạt động chiến đấu trên biển"),
            ("Uyên ương", "Chim uyên ương, loài chim nước nổi tiếng với bộ lông đẹp và sự thủy chung"),
            ("Tượng", "Con voi, loài vật khổng lồ có vai trò quan trọng trong biên chế quân đội nhà Nguyễn"),
        ]
    },
    "tuyen-dinh": {
        "file": "11_Data_TuyenDinh.json",
        "urn_name_vi": "Tuyên Đỉnh",
        "urn_name_en": "The Urn of Proclamation",
        "urn_description": "Thụy hiệu của vua Khải Định",
        "motifs": [
            ("Tuyên đỉnh", "Thụy hiệu của vua Khải Định"),
            ("Tần cát liễu", "Chim yểng, loài chim cảnh nổi tiếng với khả năng nhại tiếng người"),
            ("Yến oa", "Tổ yến, một sản vật tiến vua quý giá thường được khai thác ở các vách đá cheo leo bên bờ biển"),
            ("Long nhãn", "Cây/quả long nhãn, một sản vật tiến vua thời xưa"),
            ("Trân châu hoa", "Hoa sói trắng, loài hoa nhỏ mọc thành chùm như chuỗi hạt trân châu, mùi thơm dịu"),
            ("Địa đậu", "Cây lạc hay đậu phộng, một loại ngũ cốc quen thuộc ở Việt Nam"),
            ("Bá", "Cây trắc bá diệp, loài cây vừa được trồng làm cảnh, vừa là loại dược liệu đa dụng"),
            ("Duệ sơn", "Núi Duệ hay núi Lễ, là một danh thắng của đất Hương Trà ở xứ Huế"),
            ("Nhĩ hà", "Sông Nhĩ, tức sông Hồng, hệ thống sông lớn nhất của miền Bắc"),
            ("Vân", "Mây"),
            ("Đại Lãnh", "Mũi Đại Lãnh, một mỏm núi đâm ra biển, danh thắng của đất Phú Yên"),
            ("Lam giang", "Sông Lam, dòng sông cùng với núi Hồng Lĩnh được coi là biểu tượng của xứ Nghệ"),
            ("Hậu ngư", "Con sam, một hải sản quý được khai thác ở một số vùng biển của Việt Nam"),
            ("Khương", "Cây gừng, loài cây được trồng lấy củ làm gia vị hoặc dược liệu"),
            ("Nỗ", "Cái nỏ, một loại vũ khí tầm xa được quân đội nhà Nguyễn sử dụng"),
            ("Lê thuyền", "Một loại thuyền có 12 tay chèo, được đón khá nhiều dưới thời vua Gia Long, Minh Mạng"),
            ("Thỉ", "Con lợn, một gia súc được nuôi lấy thịt rất quen thuộc ở vùng nông thôn Việt Nam"),
            ("Ngoan", "Con vích, loài rùa biển cỡ nhỏ thường được khai thác để lấy thịt và mai làm đồ mỹ nghệ"),
        ]
    },
    "nhan-dinh": {
        "file": "06_Data_NhanDinh.json",
        "urn_name_vi": "Nhân Đỉnh",
        "urn_name_en": "The Benevolence Urn",
        "urn_description": "Truy hiệu của vua Minh Mạng",
        "motifs": [
            ("Nhân đỉnh", "Truy hiệu của vua Minh Mạng"),
            ("Ngô đồng", "Cây ngô đồng, loài cây được trồng khá nhiều ở kinh thành Huế"),
            ("Kỳ nam", "Gỗ kỳ nam, loại trầm hương phẩm chất cao nhất, hết sức quý hiếm"),
            ("Noa", "Cây lúa nếp, giống lúa dẻo và thơm song hành cùng lúa tẻ trên các ruộng lúa Việt Nam"),
            ("Nam trân", "Cây bòn bon, loài cây cho quả từng cứu sống chúa Nguyễn Ánh khi ẩn náu trong rừng"),
            ("Liên hoa", "Hoa sen, loài hoa tượng trưng cho sự cao quý bất chấp nghịch cảnh"),
            ("Khổng tước", "Chim công, loài chim có bộ lông rực rỡ được mệnh danh là nữ hoàng của các loài chim"),
            ("Nam Hải", "Vùng biển phía Nam nước Việt"),
            ("Phổ Lợi hà", "Con sông do vua Minh Mạng cho đào năm 1835, nối sông Hương với cửa biển Thuận An"),
            ("Nguyệt", "Mặt trăng"),
            ("Hương giang", "Sông Hương, dòng sông biểu tượng chảy qua kinh thành Huế"),
            ("Ngự Bình sơn", "Núi Ngự Bình, có hình dáng như bức bình phong, cùng với sông Hương tạo thành cảnh quan đặc trưng của Huế"),
            ("Nhân ngư", "Cá voi, loài cá thiêng phù trợ người đi biển theo quan niệm của người dân miền biển"),
            ("Cửu", "Cây hẹ, một loại cây gia vị gần gũi với hành"),
            ("Lâu thuyền", "Thuyền lầu, loại thuyền nhiều tầng thường được dùng cho nhà vua và người hoàng tộc"),
            ("Luân xa pháo", "Súng đại bác đặt trên xe, phiên bản cơ động của súng đại bác"),
            ("Báo", "Con báo, loài vật họ mèo chỉ đứng dưới con hổ về độ 'hổ báo' trong rừng rậm Việt Nam"),
            ("Đại mạo", "Con đồi mồi, loại rùa biển có mai đẹp, thịt ngon, là sản vật quý tiến vua"),
        ]
    },
    "anh-dinh": {
        "file": "08_Data_AnhDinh.json",
        "urn_name_vi": "Anh Đỉnh",
        "urn_name_en": "The Urn of Brilliance",
        "urn_description": "Thụy hiệu của vua Tự Đức",
        "motifs": [
            ("Anh đỉnh", "Thụy hiệu của vua Tự Đức"),
            ("Thiền", "Con ve, loài côn trùng gắn liền với mùa hạ ở Việt Nam"),
            ("Tô hợp", "Cây tô hợp, loài cây thuốc quý trong Đông y"),
            ("Uất kim", "Cây nghệ, loài cây cho củ vừa dùng làm gia vị, vừa là dược liệu"),
            ("Tân lang", "Cây cau, loài cây thường được trồng làm cảnh và thu hoạch quả ở vùng quê Việt"),
            ("Khôi hạc", "Chim hạc, một loài chim được coi là có tính cách của người quân tử"),
            ("Mai khôi hoa", "Cây hoa hồng, loài cây cho hoa thơm và đẹp, được trồng phổ biến trong các khu vườn xưa"),
            ("Ngân hán", "Dải ngân hà"),
            ("Mã giang", "Sông Mã, một con sông lớn ở miền Bắc"),
            ("Bắc Đẩu", "Sao Bắc Đẩu, chòm sao gồm 7 ngôi sao nằm ở phương Bắc, được dùng xác định phương hướng"),
            ("Lô hà", "Sông Lô, phụ lưu tả ngạn của sông Hồng ở khu vực miền núi phía Bắc"),
            ("Hồng sơn", "Núi Hồng Lĩnh, dãy núi nổi tiếng được coi là hồn thiêng của xứ Nghệ"),
            ("Mã", "Con ngựa, loài gia súc được sử dụng làm phương tiện vận chuyển thời xưa"),
            ("Tang", "Cây dâu tằm, loài cây gắn liền với nghề dệt của người Việt"),
            ("Kỳ", "Lá cờ"),
            ("Hồ điệp tử", "Đạn bươm bướm, loại đạn đại pháo khi nổ bung ra tứ phía trông như tổ kén của con bướm"),
            ("Nhiêm xà", "Con trăn, loài bò sát khổng lồ sinh sống trong nhiều vùng rừng rậm của Việt Nam"),
            ("Tử mộc", "Cây gỗ kiến, loài cây được sử dụng để sản xuất sơn cánh kiến"),
        ]
    },
    "du-dinh": {
        "file": "12_Data_DuDinh.json",
        "urn_name_vi": "Dụ Đỉnh",
        "urn_name_en": "The Urn of Abundance",
        "urn_description": "Tên không phải là thụy hiệu của bất kì vị vua nào triều Nguyễn",
        "motifs": [
            ("Dụ đỉnh", "Tên không phải là thụy hiệu của bất kì vị vua nào triều Nguyễn"),
            ("Anh vũ", "Chim vẹt, loài chim rất giỏi nhại tiếng người"),
            ("Lê", "Cây lê, loài cây được trồng để lấy quả tại một số vùng của Việt Nam"),
            ("Phù lưu", "Cây trầu, loại cây leo được trồng lấy lá, gắn bó với tục ăn trầu của người Việt"),
            ("Bạch đầu", "Cây đậu trắng, loài ngũ cốc họ đậu"),
            ("Thuần hoa", "Cây hoa dâm bụt, loài cây có hoa đỏ rất đẹp thường được trồng làm hàng rào"),
            ("Tùng", "Cây tùng, loại cây lá kim tượng trưng cho sự trường tồn, vĩnh cửu"),
            ("Hải vân quan", "Cửa ải Hải Vân, một cửa ải quan trọng trấn giữ đường thiên lý Bắc – Nam"),
            ("Vĩnh Điện hà", "Sông Vĩnh Điện, con sông chảy qua đất Quảng Nam – Đà Nẵng"),
            ("Lôi", "Sấm"),
            ("Vệ giang", "Sông Vệ, một con sông nằm ở Quảng Ngãi"),
            ("Đà Nẵng hải khẩu", "Cửa biển Đà Nẵng, chính là cửa Hàn, cửa biển có vai trò chiến lược"),
            ("Thạch thủ ngư", "Cá mú, loài cá biển có thịt ngon được khai thác tại nhiều vùng biển"),
            ("Tử tô", "Cây tía tô, loài cây bụi có lá màu tím, được dùng làm gia vị và dược liệu"),
            ("Ô thuyền", "Loại thuyền đi biển sơn màu đen, cánh buồm cũng đen, có 12 tay chèo"),
            ("Phác đạo", "Loại đao có cán dài, thường được trang bị cho binh lính trận mạc"),
            ("Cáp", "Con sò, loài hải sản có họ với con ngao"),
            ("Dương", "Con dê, loài gia súc được nuôi nhiều tại một số vùng núi đá của Việt Nam"),
        ]
    },
    "huyen-dinh": {
        "file": "13_Data_HuyenDinh.json",
        "urn_name_vi": "Huyền Đỉnh",
        "urn_name_en": "The Urn of Mystery",
        "urn_description": "Tên không phải là thụy hiệu của bất kì vị vua nào trong triều Nguyễn",
        "motifs": [
            ("Huyền đỉnh", "Tên không phải là thụy hiệu của bất kì vị vua nào trong triều Nguyễn"),
            ("Ngũ điệp lan", "Cây ngọc lan, một loài cây thân gỗ thường được trồng trong vườn lấy bóng mát, có hoa rất thơm"),
            ("Lệ chi", "Cây vải, loài cây trồng lấy quả làm đặc sản tiến vua của một số địa phương ở đồng bằng sông Hồng"),
            ("Toán", "Cây tỏi, cây gia vị có họ với cây hành, hẹ, kiệu"),
            ("Nam sâm", "Cây sâm ta, một dược liệu quý của Việt Nam"),
            ("Miên", "Cây bông, loài cây trồng lấy sợi phục vụ ngành dệt"),
            ("Thốc thu", "Chim phù lão hay chim già đẫy, một loài chim trọc đầu sinh sống tại các vùng ngập nước Nam Bộ"),
            ("Hồng", "Cầu vồng"),
            ("Hậu giang, Tiền giang", "Sông Tiền và Sông Hậu, hai dòng sông chính của đồng bằng sông Cửu Long"),
            ("Vũ", "Mưa"),
            ("Hoàng sơn", "Đèo Ngang, con đèo nằm ở ranh giới Hà Tĩnh và Quảng Bình"),
            ("Thao hà", "Sông Thao, dòng sông lớn có vai trò quan trọng với giao thông và thủy lợi ở đất tổ Phú Thọ"),
            ("Quế đỏ", "Con cà cuống, loài côn trùng lớn sống dưới nước, được khai thác lấy tinh dầu làm gia vị"),
            ("Xa", "Xe"),
            ("Mãng xà", "Con mãng xà, theo quan niệm dân gian là loài rắn lớn nhất, vua của các loài rắn"),
            ("Hỏa phún đồng", "Ống phun lửa, một loại hỏa khí của quân đội nhà Nguyễn"),
            ("Sơn mã", "Con mang, một loài hươu nhỏ sinh sống trong nhiều khu rừng ở Việt Nam"),
            ("Tất mộc", "Cây sơn, nguyên liệu làm sơn ta, vật liệu quý thường được dùng để sơn phủ đồ gỗ"),
        ]
    },
    "cao-dinh": {
        "file": "05_Data_CaoDinh.json",
        "urn_name_vi": "Cao Đỉnh",
        "urn_name_en": "The Urn of Height",
        "urn_description": "Thụy hiệu của vua Gia Long",
        "motifs": [
            ("Cao đỉnh", "Thụy hiệu của vua Gia Long"),
            ("Long", "Con rồng, biểu tượng cho quyền lực của hoàng đế"),
            ("Ba la mật", "Cây mít, loài cây ăn quả quen thuộc ở các làng quê Việt Nam"),
            ("Canh", "Cây lúa tẻ, nông sản gắn liền với nền sản xuất của người Việt từ xa xưa"),
            ("Thông", "Cây hành, loại rau gia vị quen thuộc của người Việt"),
            ("Tử vi hoa", "Hoa tường vi, một loài hoa mọc thành chùm màu tím rất đẹp"),
            ("Trĩ", "Chim trĩ, loài chim có họ với gà, sở hữu bộ lông màu sắc rất đẹp"),
            ("Đông Hải", "Biển Đông, vùng biển gắn với chủ quyền thiêng liêng của Việt Nam"),
            ("Vĩnh Tế hà", "Kênh Vĩnh Tế, con kênh đào vĩ đại ở khu vực đồng bằng sông Cửu Long được vua Gia Long cho khởi công năm 1819"),
            ("Nhật", "Mặt trời"),
            ("Ngưu Chữ giang", "Kênh Bến Nghé, một huyết mạch giao thông đường thủy ở Sài Gòn – Gia Định"),
            ("Thiên Tôn sơn", "Núi Thiên Tôn ở thôn Gia Miêu, Thanh Hóa, nơi phát tích của vương triều Nguyễn"),
            ("Thiết mộc", "Cây gỗ lim, loại cây cho gỗ rất cứng và bền, thường được dùng làm cột đình, chùa, cung điện"),
            ("Hổ", "Con hổ, loài vật biểu tượng cho sức mạnh, phân bố trong hầu khắp các khu rừng rậm ở Việt Nam xưa"),
            ("Đa tác thuyền", "Thuyền buồm, loại thuyền đi biển đường dài có xuất xứ phương Tây"),
            ("Đại bác", "Súng đại bác, hỏa khí chủ lực trong quân đội Nhà Nguyễn"),
            ("Trầm hương", "Cây trầm hương, một loài cây cho gỗ có mùi thơm rất quý hiếm"),
            ("Miết", "Con ba ba, một thủy sản có giá trị được khai thác tại nhiều sông hồ của Việt Nam"),
        ]
    },
    "chuong-dinh": {
        "file": "07_Data_ChuongDinh.json",
        "urn_name_vi": "Chương Đỉnh",
        "urn_name_en": "The Urn of Distinction",
        "urn_description": "Thụy hiệu của vua Thiệu Trị",
        "motifs": [
            ("Chương đỉnh", "Thụy hiệu của vua Thiệu Trị"),
            ("Mạt lị", "Hoa nhài, loài hoa thơm được trồng phổ biến trong các khu vườn của người Việt"),
            ("Am la", "Cây xoài, một loại cây ăn trái quen thuộc của Việt Nam"),
            ("Đậu khấu", "Cây đậu khấu, loại cây có quả được sử dụng làm vị thuốc quý trong Đông dược"),
            ("Lục đậu", "Cây đậu xanh, loại ngũ cốc có vai trò quan trọng trong nền ẩm thực Việt"),
            ("Giới", "Cây kiệu, loại rau gia vị có họ với hành, hẹ"),
            ("Kê", "Con gà, loài gia cầm gắn liền với mọi xóm làng của người Việt"),
            ("Thượng sơn", "Núi Thượng, tức núi Kim Phụng, một danh thắng nằm ở Hương Trà, Huế"),
            ("Lợi Nông hà", "Sông Lợi Nông, tức sông An Cựu, chi lưu của sông Hương ở phía Nam kinh thành Huế"),
            ("Ngũ tinh", "Sao Mộc, sao Hỏa, sao Thổ, sao Kim, sao Thủy, các tinh tú có vai trò quan trọng trong thiên văn cổ"),
            ("Linh Giang", "Sông Gianh, dòng sông ở Quảng Bình từng là ranh giới giữa Đàng Trong và Đàng Ngoài"),
            ("Tây Hải", "Vùng biển phía Tây nước Việt"),
            ("Thuận mộc", "Cây gỗ huỳnh, hay gỗ sưa"),
            ("Ngạc ngư", "Con cá sấu, loài bò sát khổng lồ sinh sống tại nhiều vùng ngập nước ở Nam Bộ thời xưa"),
            ("Mông đồng thuyền", "Mẫu thuyền chiến cơ động có đáy nông, nhiều tay chèo, trang bị nỏ mạnh"),
            ("Điểu thương", "Loại súng hỏa mai được sử dụng phổ biến trong quân đội nhà Nguyễn"),
            ("Tê", "Con tê giác, loài động vật quý hiếm ngày nay đã tuyệt chủng ở Việt Nam"),
            ("Linh quy", "Rùa thiêng, một linh vật trong tín ngưỡng dân gian Việt Nam"),
        ]
    },
}


def generate_quiz(name_vi: str, description: str, idx: int) -> dict:
    """Generate a simple quiz question for a motif."""
    return {
        "question": f"Bản đúc nổi '{name_vi}' trên Cửu Đỉnh có ý nghĩa gì?",
        "options": [
            f"A. {description[:80]}..." if len(description) > 80 else f"A. {description}",
            "B. Một loài thực vật quý hiếm",
            "C. Một địa danh lịch sử",
            "D. Một biểu tượng văn hóa"
        ],
        "correct_answer": f"A. {description[:80]}..." if len(description) > 80 else f"A. {description}"
    }


def slugify(text: str) -> str:
    """Convert Vietnamese text to slug."""
    import unicodedata
    import re
    text = unicodedata.normalize('NFD', text)
    text = ''.join(c for c in text if unicodedata.category(c) != 'Mn')
    text = text.lower().strip()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[-\s]+', '-', text)
    return text


def create_json_data(urn_slug: str, data: dict) -> list:
    """Create JSON data structure for an urn."""
    items = []
    urn_name = data["urn_name_vi"]

    for idx, (name_vi, description) in enumerate(data["motifs"], 1):
        item_id = f"urn_{urn_slug.replace('-', '_')}_{idx:02d}"
        mesh_name = name_vi.title()

        # Determine thumbnail URL
        urn_dir = urn_name.upper().replace("Đ", "D").replace(" ", "%20")
        motif_file = name_vi.upper()
        thumbnail_url = f"/assets/ban-duc-noi/{urn_dir}/{motif_file}.jpg"

        item = {
            "id": item_id,
            "name_vi": name_vi.title(),
            "name_en": data["urn_name_en"] if idx == 1 else None,
            "urn_location": urn_name,
            "description_short": description,
            "description_educational": description,
            "quiz_question": generate_quiz(name_vi, description, idx),
            "3d_mesh_id": f"mesh_{item_id}_v1",
            "thumbnail_url": thumbnail_url
        }
        items.append(item)

    return items


def main():
    data_dir = Path(__file__).parent.parent / "data"

    for urn_slug, data in MOTIF_DATA.items():
        filename = data["file"]
        filepath = data_dir / filename

        json_data = create_json_data(urn_slug, data)

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(json_data, f, ensure_ascii=False, indent=2)

        print(f"✅ Updated {filename} with {len(json_data)} motifs")

    print(f"\n✅ All 9 đỉnh JSON files updated!")
    print("Next step: Run 'docker compose exec api python -m backend.seed' to update database")


if __name__ == "__main__":
    main()

