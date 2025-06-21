// dao_governor.mjs

import { ethers } from "ethers";
import DAOAbi from "../contracts/AutonomousMaintenanceDAO.json";

// Validate all required environment variables
function validateEnv() {
  const requiredVars = [
    "ETH_NODE_URL",
    "DAO_PRIVATE_KEY",
    "DAO_ADDRESS",
    "DAO_QUORUM"
  ];
  for (const varName of requiredVars) {
    if (!process.env[varName]) {
      throw new Error(`❌ Missing environment variable: ${varName}`);
    }
  }
}

validateEnv();

const provider = new ethers.providers.JsonRpcProvider(process.env.ETH_NODE_URL);
const wallet = new ethers.Wallet(process.env.DAO_PRIVATE_KEY, provider);
const daoContract = new ethers.Contract(process.env.DAO_ADDRESS, DAOAbi, wallet);

const executedProposals = new Set();

async function checkPendingVotes() {
  try {
    const proposals = await daoContract.getPendingProposals();

    for (const proposal of proposals) {
      if (executedProposals.has(proposal.id)) continue;

      const votes = await daoContract.getVotes(proposal.id);
      const quorum = ethers.BigNumber.from(process.env.DAO_QUORUM);

      if (votes.gte(quorum)) {
        try {
          await daoContract.executeUpgrade(proposal.id);

          // Optional: Track deployed patch hash
          if (daoContract.getPatchCID) {
            const cid = await daoContract.getPatchCID(proposal.id);
            console.log(`✅ Upgrade executed for Proposal ${proposal.id} (IPFS patch: ${cid})`);
          } else {
            console.log(`✅ Upgrade executed for Proposal ${proposal.id}`);
          }

          executedProposals.add(proposal.id);
        } catch (err) {
          console.error(`⚠️ Execution failed for Proposal ${proposal.id}: ${err.message}`);
        }
      }
    }
  } catch (err) {
    console.error("❌ Error checking proposals:", err.message);
  }
}

async function listenForProposals() {
  daoContract.on("NewProposal", (proposalId) => {
    console.log(`🆕 New DAO Proposal Detected: ${proposalId}`);
  });
}

async function main() {
  await listenForProposals();
  await checkPendingVotes(); // Initial check at startup
  setInterval(checkPendingVotes, 60 * 60 * 1000); // Every hour
}

main().catch(console.error);