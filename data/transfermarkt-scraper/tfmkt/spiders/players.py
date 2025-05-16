from tfmkt.spiders.common import BaseSpider
from scrapy.shell import Response
from scrapy.shell import inspect_response  # required for debugging
from urllib.parse import unquote, urlparse
import scrapy
import re
import json

class PlayersSpider(BaseSpider):
    name = 'players'

    def parse(self, response, parent):
        players_table = response.xpath("//div[@class='responsive-table']")
        assert len(players_table) == 1
        players_table = players_table[0]
        player_hrefs = players_table.xpath('//table[@class="inline-table"]//td[@class="hauptlink"]/a/@href').getall()

        for href in player_hrefs:
            cb_kwargs = {
                'base': {
                    'type': 'player',
                    'href': href,
                    'parent': parent
                }
            }
            yield response.follow(href, self.parse_details, cb_kwargs=cb_kwargs)

    def parse_details(self, response, base):
        attributes = {}
        name_element = response.xpath("//h1[@class='data-header__headline-wrapper']")
        attributes["name"] = self.safe_strip("".join(name_element.xpath("text()").getall()).strip())
        attributes["last_name"] = self.safe_strip(name_element.xpath("strong/text()").get())
        attributes["number"] = self.safe_strip(name_element.xpath("span/text()").get())

        attributes['name_in_home_country'] = response.xpath("//span[text()='Name in home country:']/following::span[1]/text()").get()
        attributes['date_of_birth'] = response.xpath("//span[@itemprop='birthDate']/text()").get().strip().split(" (")[0]
        attributes['place_of_birth'] = {
            'country': response.xpath("//span[text()='Place of birth:']/following::span[1]/span/img/@title").get(),
            'city': response.xpath("//span[text()='Place of birth:']/following::span[1]/span/text()").get()
        }
        attributes['age'] = response.xpath("//span[@itemprop='birthDate']/text()").get().strip().split('(')[-1].split(')')[0]
        attributes['height'] = response.xpath("//span[text()='Height:']/following::span[1]/text()").get()
        attributes['citizenship'] = response.xpath("//span[text()='Citizenship:']/following::span[1]/img/@title").get()
        attributes['position'] = self.safe_strip(response.xpath("//span[text()='Position:']/following::span[1]/text()").get())
        attributes['player_agent'] = {
            'href': response.xpath("//span[text()='Player agent:']/following::span[1]/a/@href").get(),
            'name': response.xpath("//span[text()='Player agent:']/following::span[1]/a/text()").get()
        }
        attributes['image_url'] = response.xpath("//img[@class='data-header__profile-image']/@src").get()
        attributes['current_club'] = {
            'href': response.xpath("//span[contains(text(),'Current club:')]/following::span[1]/a/@href").get()
        }
        attributes['foot'] = response.xpath("//span[text()='Foot:']/following::span[1]/text()").get()
        attributes['joined'] = response.xpath("//span[text()='Joined:']/following::span[1]/text()").get()
        attributes['contract_expires'] = self.safe_strip(response.xpath("//span[text()='Contract expires:']/following::span[1]/text()").get())
        attributes['day_of_last_contract_extension'] = response.xpath("//span[text()='Date of last contract extension:']/following::span[1]/text()").get()
        attributes['outfitter'] = response.xpath("//span[text()='Outfitter:']/following::span[1]/text()").get()

        social_media_value_node = response.xpath("//span[text()='Social-Media:']/following::span[1]")
        if len(social_media_value_node) > 0:
            attributes['social_media'] = []
            for element in social_media_value_node.xpath('div[@class="socialmedia-icons"]/a'):
                href = element.xpath('@href').get()
                attributes['social_media'].append(href)

        attributes['code'] = unquote(urlparse(base["href"]).path.split("/")[1])

        response.meta['base'] = {
            **base,
            **attributes
        }

        player_id = base['href'].split('/')[-1]

        yield scrapy.Request(
            url=f"https://www.transfermarkt.co.uk/ceapi/transferHistory/list/{player_id}",
            callback=self.parse_transfer_history,
            meta={'base': response.meta['base'], 'player_id': player_id},
            headers={'Accept': 'application/json'}
        )

    def parse_transfer_history(self, response):
        base = response.meta['base']
        player_id = response.meta['player_id']

        try:
            data = json.loads(response.text)
            base['transfer_history'] = data.get('transfers', [])
        except Exception as e:
            self.logger.warning(f"Failed to fetch transfer history from {response.url}: {e}")
            base['transfer_history'] = None

        yield scrapy.Request(
            url=f"https://www.transfermarkt.co.uk/ceapi/marketValueDevelopment/graph/{player_id}",
            callback=self.parse_market_value_history,
            meta={'base': base},
            headers={'Accept': 'application/json'}
        )

    def parse_market_value_history(self, response):
        base = response.meta['base']

        try:
            data = json.loads(response.text)
            base['market_value_history'] = data.get('list', [])
            base['current_market_value'] = data.get('current')
            base['highest_market_value'] = data.get('highest')
        except Exception as e:
            self.logger.warning(f"Failed to fetch market value history from {response.url}: {e}")
            base['market_value_history'] = None

        yield base