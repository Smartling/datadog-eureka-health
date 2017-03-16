import time
import requests
import pdb
import DNS
from checks import AgentCheck
from lxml import etree

class SleurekaCheck(AgentCheck):

  def check(self, instance):
    # if DNS domain for eureka instance not specified -- skip instance
    if 'domain' not in instance:
      self.log.info('Skipping instance, no domain found.')
      return

    # Parsing eureka instance details, setting defaults if necessary
    protocol = instance.get('protocol', 'http')
    port = int(instance.get('port', 8080))
    context = instance.get('context','/eureka/v2')
    region = instance.get('region', 'us-east-1')
    timeout = float(instance.get('timeout', 5))
    essential_applications = instance.get('essential_applications', [])
    tags = instance.get('tags', [])

    eureka_nodes = self.get_eureka_nodes(region, instance)

    # Number of nodes found in Eureka dns setup
    self.gauge('eureka.nodes_num', len(eureka_nodes), tags=tags)

    # Check every node found in dns setup
    for eureka_node_name in eureka_nodes:
      eureka_node = {
        'name': eureka_node_name,
        'protocol': protocol,
        'port': port,
        'context': context,
        'timeout': timeout,
        'essential_applications': essential_applications
      }
      self.check_eureka_node(eureka_node, tags=tags)

  def check_eureka_node(self, node, tags):
    url = node['protocol'] + '://' + node['name'] + ":" + str(node['port']) + node['context'] + '/apps'

    start_time = time.time()
    try:
      r = requests.get(url, timeout=node['timeout'])
      end_time = time.time()
      response_time = end_time - start_time
      response_status = r.status_code
    except:
      response_time = 0
      response_status = 0
      return

    self.gauge('eureka.node.response_time', response_time, tags=tags + ["eureka_node_name:" + node['name']])
    self.gauge('eureka.node.response_status', response_status, tags=tags + ["eureka_node_name:" + node['name']])

    try:
      self.check_eureka_applications(r, node['name'], node['essential_applications'], tags=tags + ["eureka_node_name:" + node['name']])
    except:
      self.log.error("Failed to check eureka node " + node['name'] + " convergence")

  def check_eureka_applications(self, response, eureka_node_name, essential_applications, tags):
    try:
      xml = etree.fromstring(response.text)
      applications_raw = xml.xpath('//applications/application/name')
      applications = []
      for application in applications_raw:
        applications.append(application.text)
    except:
      self.log.error("Unable to parse applications data from Eureka node " + node_name)
      applications = []
      return

    self.gauge('eureka.node.applications_num', len(applications), tags=tags)

    eureka_convergence_status = 0 # 0: ok, 1: fail
    for essential_application in essential_applications:
      if essential_application not in applications:
        eureka_convergence_status = 1
        break

    self.gauge('eureka.node.convergence_status', eureka_convergence_status, tags=tags)

  @staticmethod
  def get_eureka_nodes(region, instance):
    try:
      available_dns_names = DNS.dnslookup('txt.' + region + '.' + instance['domain'],'txt')
      # We take first TXT record here
      if len(available_dns_names):
        nodes = []
        for dns_name in available_dns_names[0]:
          # Configuring EIPs using DNS.
          try:
            hosts = DNS.dnslookup('txt.' + dns_name,'txt')
            if len(hosts):
              for host in hosts[0]:
                nodes.append(host)
            else:
              nodes.append(dns_name)
          except DNS.ServerError as e:
            nodes.append(dns_name)
        return nodes
      else:
        return []
    except DNS.ServerError as e:
      return []

