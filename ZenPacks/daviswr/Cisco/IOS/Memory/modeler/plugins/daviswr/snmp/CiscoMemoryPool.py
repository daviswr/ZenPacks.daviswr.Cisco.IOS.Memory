__doc__ = """CiscoMemoryPool

models memory pools from a Cisco IOS device

"""

from Products.DataCollector.plugins.CollectorPlugin \
    import SnmpPlugin, GetTableMap
from Products.DataCollector.plugins.DataMaps \
    import MultiArgs, RelationshipMap, ObjectMap


class CiscoMemoryPool(SnmpPlugin):
    maptype = 'MemoryPool'
    relname = 'memoryPools'
    modname = 'ZenPacks.daviswr.Cisco.IOS.Memory.MemoryPool'

    ciscoMemoryPoolEntry = {
        # ciscoMemoryPoolName
        '.2': 'title',
        # ciscoMemoryPoolAlternate
        '.3': 'alt_idx',
        # ciscoMemoryPoolValid
        '.4': 'valid',
        # ciscoMemoryPoolUsed
        '.5': 'used',
        # ciscoMemoryPoolFree
        '.6': 'free',
        }

    snmpGetTableMaps = (
        GetTableMap(
            'ciscoMemoryPoolTable',
            '.1.3.6.1.4.1.9.9.48.1.1.1',
            ciscoMemoryPoolEntry
            ),
        )

    def condition(self, device, log):
        """determine if this modeler should run"""
        # CISCO-SMI::ciscoProducts
        if not device.snmpOid.startswith('.1.3.6.1.4.1.9.1'):
            log.info('%s is not a Cisco IOS device', device.id)
        return device.snmpOid.startswith('.1.3.6.1.4.1.9.1')

    def process(self, device, results, log):
        """collect snmp information from this device"""
        log.info('processing %s for device %s', self.name(), device.id)
        maps = list()
        getdata, tabledata = results

        log.debug('SNMP Tables:\n%s', tabledata)

        ciscoMemoryPoolTable = tabledata.get('ciscoMemoryPoolTable')
        if ciscoMemoryPoolTable is None:
            log.error('Unable to get ciscoMemoryPoolTable for %s', device.id)
        else:
            log.debug(
                'ciscoMemoryPoolTable has %s entries',
                len(ciscoMemoryPoolTable)
                )

        # Memory Pools
        rm = self.relMap()

        for snmpindex in ciscoMemoryPoolTable:
            row = ciscoMemoryPoolTable[snmpindex]
            name = row.get('title', None)

            if name is None:
                continue
            elif '' == name or len(name) == 0:
                name = 'Memory Pool {0}'.format(snmpindex)

            log.debug('%s found memory pool: %s', self.name(), name)

            # Find the name of the alternate pool's index if index > 0
            alt_row = ciscoMemoryPoolTable.get(str(row['alt_idx']), dict())
            row['alternate'] = alt_row.get('title', 'Yes') \
                if row.get('alt_idx', 0) > 0 \
                else 'None'

            if 'valid' in row:
                row['valid'] = True if row.get('valid') == 1 else False

            row['size'] = row.get('free', 0) + row.get('used', 0)

            # Update dictionary and create Object Map
            row.update({
                'snmpindex': snmpindex.strip('.'),
                'id': self.prepId('mempool_{0}'.format(name))
                })

            rm.append(ObjectMap(
                modname='ZenPacks.daviswr.Cisco.IOS.Memory.MemoryPool',
                data=row
                ))

        log.debug('%s RelMap:\n%s', self.name(), str(rm))

        return rm
