const { SkrResolver, SKR_PARENT_PK } = require("../src/resolver");
const { TldParser, getHashedName, getNameAccountKeyWithBump } = require("@onsol/tldparser");
const { PublicKey } = require("@solana/web3.js");

// Mocking dependencies
jest.mock("@onsol/tldparser", () => {
    return {
        TldParser: jest.fn().mockImplementation(() => ({
            getOwnerFromDomainTld: jest.fn()
        })),
        getHashedName: jest.fn(),
        getNameAccountKeyWithBump: jest.fn(),
        ANS_PROGRAM_ID: "mock-program-id"
    };
});

jest.mock("@solana/web3.js", () => {
    return {
        PublicKey: jest.fn().mockImplementation((val) => ({
            toBase58: () => val,
            toString: () => val
        })),
        Connection: jest.fn()
    };
});

describe("SkrResolver", () => {
    let mockConnection;
    let resolver;

    beforeEach(() => {
        mockConnection = {};
        resolver = new SkrResolver(mockConnection);
        jest.clearAllMocks();
    });

    describe("Constructor", () => {
        test("should throw error if connection is not provided", () => {
            expect(() => new SkrResolver(null)).toThrow("Connection is required");
        });

        test("should instantiate TldParser", () => {
            TldParser.mockClear();
            new SkrResolver(mockConnection);
            expect(TldParser).toHaveBeenCalledWith(mockConnection);
        });
    });

    describe("resolve()", () => {
        test("should throw error if domain is not a string or empty", async () => {
            await expect(resolver.resolve("")).rejects.toThrow("Valid domain string is required");
            await expect(resolver.resolve(null)).rejects.toThrow("Valid domain string is required");
            await expect(resolver.resolve(123)).rejects.toThrow("Valid domain string is required");
        });

        test("should throw error if domain name is invalid (whitespace only)", async () => {
            await expect(resolver.resolve("   ")).rejects.toThrow("Invalid domain name");
            await expect(resolver.resolve(".skr")).rejects.toThrow("Invalid domain name");
        });

        test("should resolve domain correctly with .skr suffix", async () => {
            const domain = "seeker.skr";
            const mockHashed = Buffer.from("hashed");
            const mockAccountKey = { toBase58: () => "AccountKey555" };
            const mockOwner = { toBase58: () => "OwnerKey888" };

            getHashedName.mockResolvedValue(mockHashed);
            getNameAccountKeyWithBump.mockReturnValue([mockAccountKey]);
            resolver.parser.getOwnerFromDomainTld.mockResolvedValue(mockOwner);

            const result = await resolver.resolve(domain);

            expect(result).toEqual({
                domain: "seeker.skr",
                accountKey: "AccountKey555",
                owner: "OwnerKey888"
            });
            expect(getHashedName).toHaveBeenCalledWith("seeker");
            expect(getNameAccountKeyWithBump).toHaveBeenCalledWith(mockHashed, undefined, expect.anything());
            expect(resolver.parser.getOwnerFromDomainTld).toHaveBeenCalledWith("seeker.skr");
        });

        test("should resolve domain correctly without suffix (adds .skr)", async () => {
            const domain = "MSFT "; // Testing case-insensitivity and trim
            const mockHashed = Buffer.from("hashed");
            const mockAccountKey = { toBase58: () => "AccountKeyMSFT" };

            getHashedName.mockResolvedValue(mockHashed);
            getNameAccountKeyWithBump.mockReturnValue([mockAccountKey]);
            resolver.parser.getOwnerFromDomainTld.mockResolvedValue(null);

            const result = await resolver.resolve(domain);

            expect(result).toEqual({
                domain: "msft.skr",
                accountKey: "AccountKeyMSFT",
                owner: null
            });
            expect(getHashedName).toHaveBeenCalledWith("msft");
        });

        test("should handle resolution failure", async () => {
            getHashedName.mockRejectedValue(new Error("RPC Error"));

            await expect(resolver.resolve("fail")).rejects.toThrow("Seeker ID Resolution failed: RPC Error");
        });
    });
});
