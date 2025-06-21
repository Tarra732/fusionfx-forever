// dao_governor.mjs

import { ethers } from "ethers";
import DAOAbi from "../contracts/AutonomousMaintenanceDAO.json";

const provider = new ethers.providers.JsonRpcProvider(process.env.ETH_NODE_URL);
const wallet = new ethers.Wallet(process.env.DAO_PRIVATE_KEY, provider);

const daoContract = new ethers.Contract(process.env.DAO_ADDRESS, DAOAbi, wallet);

async function checkPendingVotes() {
  const proposals = await daoContract.getPendingProposals();
  for (const proposal of proposals) {
    const votes = await daoContract.getVotes(proposal.id);
    if (votes >= process.env.DAO_QUORUM) {
      await daoContract.executeUpgrade(proposal.id);
      console.log(`Executed upgrade proposal ${proposal.id}`);
    }
  }
}

async function listenForProposals() {
  daoContract.on("NewProposal", (proposalId) => {
    console.log(`New proposal detected: ${proposalId}`);
  });
}

async function main() {
  await listenForProposals();
  setInterval(checkPendingVotes, 60 * 60 * 1000); // check every hour
}

main().catch(console.error);