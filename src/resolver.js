const { TldParser, getHashedName, getNameAccountKeyWithBump } = require("@onsol/tldparser");
const { PublicKey } = require("@solana/web3.js");

/**
 * Seeker ID (.skr) Resolver
 * Parent TLD: F3A8kuikEiu6k2399oSJ1PWfcJYDHqpwoQ2e8psSDNuF
 */
const SKR_PARENT_PK = new PublicKey("F3A8kuikEiu6k2399oSJ1PWfcJYDHqpwoQ2e8psSDNuF");

class SkrResolver {
    /**
     * @param {import("@solana/web3.js").Connection} connection 
     */
    constructor(connection) {
        if (!connection) {
            throw new Error("Connection is required");
        }
        this.connection = connection;
        this.parser = new TldParser(connection);
    }

    /**
     * Resolves a Seeker ID domain to its account key and owner.
     * @param {string} domain - Domain name (e.g., "msft" or "msft.skr")
     * @returns {Promise<{domain: string, accountKey: string, owner: string|null}>}
     */
    async resolve(domain) {
        if (!domain || typeof domain !== 'string') {
            throw new Error("Valid domain string is required");
        }

        const cleanDomain = domain.toLowerCase().trim();
        const name = cleanDomain.endsWith(".skr") ? cleanDomain.slice(0, -4) : cleanDomain;

        if (!name) {
            throw new Error("Invalid domain name");
        }

        try {
            // 1. Derive the account key
            const hashedName = await getHashedName(name);
            const [accountKey] = getNameAccountKeyWithBump(
                hashedName,
                undefined,
                SKR_PARENT_PK
            );

            // 2. Fetch the owner using the TLD parser
            const owner = await this.parser.getOwnerFromDomainTld(`${name}.skr`);

            return {
                domain: `${name}.skr`,
                accountKey: accountKey.toBase58(),
                owner: owner ? owner.toBase58() : null
            };
        } catch (error) {
            // Re-throw with more context if needed, or just keep it clean
            throw new Error(`Seeker ID Resolution failed: ${error.message}`);
        }
    }
}

module.exports = { SkrResolver, SKR_PARENT_PK };
